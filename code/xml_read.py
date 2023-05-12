
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mar 23 2023

@author: maximiliankarlander
"""
import argparse
from argparse import RawTextHelpFormatter
import xml.etree.ElementTree as ET
import math
import gzip
import os
import shutil
"""
gzip -cd can\ anybody\ hear\ me.als > can\ anybody\ hear\ me.xml

- add errors and explanations


- extract grouped instruments
- extract send values from Ableton
- extract reverb and delay settings?
- extract volumes from Ableton
- extract poly
"""

def read_project(file):
    file_content = gzip.open(file, 'rb')
    tree = ET.parse(file_content)
    root = tree.getroot()
    return(root)

def track_tempo_extractor(root):
    for i in range(len(root[0])):
        if root[0][i].tag == 'Tracks':
            tracks = root[0][i]
    for child in root[0]:
        if child.tag == 'MasterTrack':
            tempo = child[-1][6][25][1].attrib['Value']
    return(tracks, tempo)

def device_extract(track, track_count):
    device_dict = {}
    print(f'Track {track_count}, track type: {track.tag}')
    for param in track:
        if param.tag == 'DeviceChain':
            for chain in param:
                if chain.tag == 'DeviceChain':
                    for devices in chain:
                        count=1
                        for device in devices:
                            print(f'Device {count}: {device.tag}')
                            count+=1
                            device_dict[device.tag] = device
    return(device_dict, track.tag)

def sampler_extract(device):
    params = {}
    #Finding sample name and location
    #sample_name = device[15][0][0][0][18][0][3].attrib['Value']
    #path_finder = device[15][0][0][0][18][0][7][0]
    MultiSampleParts = device[15][0][0]
    sample_names = []
    filepaths = []
    rootkeys = []
    keyrangemins = []
    keyrangemaxs = []
    for i in range(len(MultiSampleParts)):
        MultiSample_name = MultiSampleParts[i][18][0][3].attrib['Value']
        MultiSample_path_finder = MultiSampleParts[i][18][0][7][0]
        RootKey = MultiSampleParts[i][8].attrib['Value']
        rootkeys.append(RootKey)
        print('Root key:', RootKey)
        KeyRangeMin = MultiSampleParts[i][5][0].attrib['Value']
        keyrangemins.append(KeyRangeMin)
        KeyRangeMax = MultiSampleParts[i][5][1].attrib['Value']
        keyrangemaxs.append(KeyRangeMax)
        print('Key range:', KeyRangeMin, '-', KeyRangeMax)
        #for i in range(len(KeyRange)):
        #    print(i, KeyRange[i].tag, KeyRange[i].attrib)
        filepath = ''
        for k in range(len(MultiSample_path_finder)):
            filepath = filepath+'/'+MultiSample_path_finder[k].attrib['Dir']
        sample_names.append(MultiSample_name)
        filepaths.append(filepath + '/' + MultiSample_name)

    params['filepath'] = filepaths
    params['rootkey'] = rootkeys
    params['keyrangemin'] = keyrangemins
    params['keyrangemax'] = keyrangemaxs
    print('Sample names:', sample_names)
    print('Sample filepaths:', params['filepath'])

    #Finding sample start and end points
    points_finder = device[15][0][0][0]
    params['sample_start'] = points_finder[14].attrib['Value']
    params['sample_end'] = points_finder[15].attrib['Value']

    print('Play start: sample', params['sample_start'])
    print('Play end: sample', params['sample_end'])

    #Finding envelope settings
    env_finder = device[19][8]
    params['attack'] = env_finder[0][1].attrib['Value']
    params['decay'] = env_finder[3][1].attrib['Value']
    params['sustain'] = env_finder[6][1].attrib['Value']
    params['release'] = env_finder[7][1].attrib['Value']
    #for i in range(len(env_finder)):
    #    print(i, env_finder[i].tag, env_finder[i].attrib)

    print('Vol Env Attack:', round(float(params['attack'])), 'ms')
    print('Vol Env Decay:', round(float(params['decay'])), 'ms')
    print('Vol Env Sustain:', round(8.6859*math.log(float(params['sustain']))), 'dB')
    print('Vol Env Release:', round(float(params['release'])), 'ms')
    
    return(params)            

def sequence_extract(track, current_track, type):
    track_sequences = []
    sequences = track[19][7][14]
    for i in range(len(sequences)):
        midiclip = sequences[i][1][0]
        if len(midiclip) > 0:
            #<TRYING TO EXTRACT SEQUENCE LENGTH>
            loopstart = midiclip[0][4][0].attrib['Value']
            loopend = midiclip[0][4][1].attrib['Value']
            clip_len = float(loopend)
            #</TRYING TO EXTRACT SEQUENCE LENGTH>
            slot_sequence = []
            steps = midiclip[0][28][0]
            slot = i+1
            slot_step = 0
            for notes in steps:
                note = notes[1].attrib['Value']
                for step in notes[0]:
                    slot_step += 1
                    current_step = {'Slot':slot, 'Step': slot_step, 'Note':note, 'Start':step.attrib['Time'], 'Duration':step.attrib['Duration'], 'Velocity':step.attrib['Velocity']}
                    slot_sequence.append(current_step)
            track_sequences.append([clip_len, slot_sequence])
    track_sequences = {'Track': current_track, 'Type': type, 'Sequences': track_sequences}   
    #print(track_sequences)
    return(track_sequences)

def clip_extract(track):
    clips = []
    ClipSlotList = track[19][7][14]
    for clip in ClipSlotList:
        AudioClip_value = clip[1][0]
        if len(AudioClip_value)>0:
            params = {}
            PathHint = AudioClip_value[0][28][0][7][0]
            sample_name = AudioClip_value[0][28][0][3].attrib['Value']
            filepath = ''
            for element in PathHint:
                filepath = filepath + '/'+ element.attrib['Dir']
            params['filepath'] = filepath + '/' + sample_name
            print('Sample name:', sample_name)
            print('Sample filepath:', params['filepath'])
            params['loop_start'] = AudioClip_value[0][4][0].attrib['Value']
            params['loop_end'] = AudioClip_value[0][4][1].attrib['Value']
            print('Loop start:', params['loop_start'])
            print('Loop end:', params['loop_end'])
            warp = AudioClip_value[0][48]
            clips.append(params)
    return(clips)
        
            #for i in range(len(loop)):
            #    print('   ', i, loop[i].tag, loop[i].attrib)

def track_iterator(tracks):
    all_params = []
    all_sequences = []
    all_clips = []
    track_count = 1
    extracted_track_count = 1
    for current_track in tracks:
        print('________________\n')
        devices, track_type = device_extract(current_track, track_count)
        if 'OriginalSimpler' in devices:
            params = sampler_extract(devices['OriginalSimpler'])
            all_params.append(params)
            current_sequences = sequence_extract(current_track, extracted_track_count, 'Sampler')
            all_sequences.append(current_sequences)
            extracted_track_count += 1
        elif 'MultiSampler' in devices:
            params = sampler_extract(devices['MultiSampler'])
            all_params.append(params)
            current_sequences = sequence_extract(current_track, extracted_track_count, 'Sampler')
            all_sequences.append(current_sequences)
            extracted_track_count += 1
        elif 'UltraAnalog' in devices:
            current_sequences = sequence_extract(current_track, 100, 'MIDI')
            all_sequences.append(current_sequences)
            #extracted_track_count += 1
        elif track_type == 'AudioTrack':
            clips = clip_extract(current_track)
            all_clips.append(clips)
        track_count += 1
    return(all_params, all_sequences, all_clips)
             
def make_output(out_path, params, manual_samples, clip_samples):
    samplelist = []
    for i in params:
        samplelist.append(i['filepath'])
    try: 
        os.mkdir(out_path)
    except:
        pass
    if not manual_samples:
        for sample in samplelist:
            if len(sample) == 1:
                sample_name = sample[0].split('/')[-1]
                destination = out_path + '/' + sample_name
                shutil.copyfile(sample[0], destination)
            else:
                multisample_path = out_path + '/' + sample[0].split('/')[-1].split('_')[0]
                try: 
                    os.mkdir(multisample_path)
                except:
                    pass
                for current_sample in sample:
                    sample_name = current_sample.split('/')[-1]
                    destination = multisample_path + '/' + sample_name
                    shutil.copyfile(current_sample, destination)
        for sample in clip_samples:
                sample_name = sample.split('/')[-1]
                destination = out_path + '/' + sample_name
                shutil.copyfile(sample, destination)

    preset_filepath = out_path + '/preset.xml'
    return(preset_filepath)

def row_column(pad):
    rc_dict = {0:[0,0], 1:[0,1], 2:[0,2], 3:[0,3],
               4:[1,0], 5:[1,1], 6:[1,2], 7:[1,3],
               8:[2,0], 9:[2,1], 10:[2,2], 11:[2,3],
               12:[3,0], 13:[3,1], 14:[3,2], 15:[3,3],
               16:[0,4], 17:[1,4], 18:[2,4], 19:[3,4]}
    rc = rc_dict[int(pad)]
    row = rc[0]
    column = rc[1]
    return(row, column)

def pad_dicter(row, column, filename, type):
    cell_dict = {'row':str(row), 'column':str(column), 'layer':"0", 'filename':filename, 'type':type}
    return(cell_dict)

def pad_params_dicter(envattack, envdecay, envsus, envrel, samstart, samlen, multisammode, loopmode, loopstart, loopend, beatcount, samtrigtype, cellmode, polymode):
    params_dict = {'gaindb': '0', 'pitch': '0', 'panpos': '0', 'samtrigtype': str(samtrigtype), 'loopmode': str(loopmode), 
                    'loopmodes': '0', 'midimode': '0', 'midioutchan': '0', 'reverse': '0', 'cellmode': str(cellmode), 
                    'envattack': str(envattack), 'envdecay': str(envdecay), 'envsus': str(envsus), 
                    'envrel': str(envrel), 'samstart': str(samstart), 'samlen': str(samlen), 'loopstart': str(loopstart), 
                    'loopend': str(loopend), 'quantsize': '3', 'synctype': '5', 'actslice': '1', 'outputbus': '1', 
                    'polymode': str(polymode), 'polymodeslice': '0', 'slicestepmode': '0', 'chokegrp': '0', 'dualfilcutoff': '0', 
                    'res': '500', 'rootnote': '0', 'beatcount': str(beatcount), 'fx1send': '0', 'fx2send': '0', 'multisammode': multisammode, 
                    'interpqual': '0', 'playthru': '0', 'slicerquantsize': '13', 'slicersync': '0', 'padnote': '0', 
                    'loopfadeamt': '0', 'lfowave': '0', 'lforate': '100', 'lfoamount': '1000', 'lfokeytrig': '0', 'lfobeatsync': '0', 
                    'lforatebeatsync': '0', 'grainsizeperc': '300', 'grainscat': '0', 'grainpanrnd': '0', 'graindensity': '600', 
                    'slicemode': '0', 'legatomode': '0', 'gainssrcwin': '0', 'grainreadspeed': '1000', 'recpresetlen': '0', 
                    'recquant': '3', 'recinput': '0', 'recinputmulti': '0', 'recusethres': '0', 'recthresh': '-20000', 'recmonoutbus': '0'}
    #polymode 1 = mono, 2 = 2 voice, 3 = 4 voice, 4 = 6 voice etc
    return(params_dict)

def empty_pad():
    params = {'gaindb': '0', 'pitch': '0', 'panpos': '0', 
              'samtrigtype': '0', 'loopmode': '0', 'loopmodes': '0', 
              'midimode': '0', 'midioutchan': '0', 'reverse': '0', 
              'cellmode': '0', 'envattack': '0', 'envdecay': '0', 
              'envsus': '1000', 'envrel': '200', 'quantsize': '3', 
              'synctype': '5', 'outputbus': '0', 'polymode': '0', 
              'polymodeslice': '0', 'slicestepmode': '0', 
              'chokegrp': '0', 'dualfilcutoff': '0', 'res': '500', 
              'rootnote': '0', 'beatcount': '0', 'fx1send': '0', 
              'fx2send': '0', 'interpqual': '0', 'playthru': '0', 
              'padnote': '0', 'deftemplate': '1', 'recpresetlen': '0', 
              'recquant': '3', 'recinput': '0', 'recinputmulti': '0', 
              'recusethres': '0', 'recthresh': '-20000', 'recmonoutbus': '0'}
    return(params)

def make_pads(from_ableton, clips, tempo):
    assets = {'filepath':[], 'rootkey':[], 'keyrangemin':[], 'keyrangemax':[], 'row':[], 'column':[]}
    root = ET.Element('document')
    session = ET.SubElement(root, 'session')
    current_pad = 0
    if len(from_ableton)>0:
        if len(from_ableton) <= 16:
            preset = len(from_ableton)
        else:
            preset = 16
        for i in range(preset):
            row, column = row_column(i)
            if float(from_ableton[i]['attack'])<1:
                attack = 1
            else:
                attack = float(from_ableton[i]['attack'])
            #FILEPATH FOR MULTISAMPLE STUFF, CHANGE
            if len(from_ableton[i]['filepath']) > 1:
                filepath = ".\\" + from_ableton[i]['filepath'][0].split('/')[-1].split('_')[0]
                for k in range(len(from_ableton[i]['filepath'])):
                    assets['filepath'].append(from_ableton[i]['filepath'][k])
                    assets['rootkey'].append(from_ableton[i]['rootkey'][k])
                    assets['keyrangemin'].append(from_ableton[i]['keyrangemin'][k])
                    assets['keyrangemax'].append(from_ableton[i]['keyrangemax'][k])
                    assets['row'].append(row)
                    assets['column'].append(column)
                    multisammode = '1'
            else:
                filepath = ".\\" + from_ableton[i]['filepath'][0].split('/')[-1]
                multisammode = '0'
            cell = ET.SubElement(session, 'cell')
            cell.attrib = pad_dicter(row, column, filepath, "sample")
            params = ET.SubElement(cell, 'params')
            params.attrib = pad_params_dicter(envattack = round(109.83000685125678*math.log(attack)), 
                                              envdecay = round(94.8286033043297*math.log(float(from_ableton[i]['decay']))), 
                                              envsus = round(float(from_ableton[i]['sustain'])*1000), 
                                              envrel = round(94.8286033043297*math.log(float(from_ableton[i]['release']))), 
                                              samstart = from_ableton[i]['sample_start'], 
                                              samlen = int(from_ableton[i]['sample_end'])-int(from_ableton[i]['sample_start']),
                                              multisammode = multisammode,
                                              loopmode = 0, 
                                              loopstart = 0, 
                                              loopend = 0, 
                                              beatcount = 0,
                                              samtrigtype = 1,
                                              cellmode = 0,
                                              polymode = 3)
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"gaindb", 'src':"velocity", 'slot':"0", 'amount':"400"}
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"gaindb", 'src':"midivol", 'slot':"2", 'amount':"1000"}
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"panpos", 'src':"midipan", 'slot':"2", 'amount':"1000"}
            slices = ET.SubElement(cell, 'slices')
            current_pad +=1
    
    clip_samples = []
    for track in clips:
        for clip in track:
            row, column = row_column(current_pad)
            cell = ET.SubElement(session, 'cell')
            filepath = '.\\' + clip['filepath'].split('/')[-1]
            clip_samples.append(clip['filepath'])
            cell.attrib = pad_dicter(row, column, filepath, "sample")
            params = ET.SubElement(cell, 'params')
            #loop_start = clip['loop_start']
            #loop_end = clip['loop_end']
            sample_rate = 48000 # <------- SAMPLE RATE ASSUMED!!!
            sample_len = round(float(clip['loop_end'])/(100/60)*sample_rate)
            params.attrib = pad_params_dicter(envattack = 0, 
                                              envdecay = 200, 
                                              envsus = 1000, 
                                              envrel = 0, 
                                              samstart = 0, 
                                              samlen = sample_len,
                                              multisammode = '0',
                                              loopmode = 1, 
                                              loopstart = 0, 
                                              loopend = sample_len, 
                                              beatcount = clip['loop_end'],
                                              samtrigtype = 2,
                                              cellmode = 1,
                                              polymode = 0)
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"gaindb", 'src':"velocity", 'slot':"0", 'amount':"400"}
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"gaindb", 'src':"midivol", 'slot':"2", 'amount':"1000"}
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"panpos", 'src':"midipan", 'slot':"2", 'amount':"1000"}
            slices = ET.SubElement(cell, 'slices')
            current_pad +=1

    for i in range(current_pad,20):
        row, column = row_column(i)
        cell = ET.SubElement(session, 'cell')
        cell.attrib = pad_dicter(row, column, '', "samtempl")
        params = ET.SubElement(cell, 'params')
        params.attrib = empty_pad()
        if i <16:
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"gaindb", 'src':"velocity", 'slot':"0", 'amount':"400"}
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"gaindb", 'src':"midivol", 'slot':"2", 'amount':"1000"}
            modsource = ET.SubElement(cell, 'modsource')
            modsource.attrib = {'dest':"panpos", 'src':"midipan", 'slot':"2", 'amount':"1000"}
        slices = ET.SubElement(cell, 'slices')
    return(root, assets, clip_samples)

def sequence_dicter(row, column, type):
    cell_dict = {'row':str(row), 'column':str(column), 'layer':"1", 'type':type}
    return(cell_dict)

def find_division(steps):
    smallest_step = False
    for_divisions = []
    for step in steps:
        if float(step['Start'])*4%1:
            smallest_step = True
            for_divisions.append(float(step['Start'])*4%1)
        if float(step['Duration'])*4%1:
            smallest_step = True
            for_divisions.append(float(step['Duration'])*4%1)
    divisions = []
    if smallest_step:
        for i in for_divisions:
            if not i%0.5:
                divisions.append(12)
            elif not i%0.25:
                divisions.append(14)
    if len(divisions)>0:
        division = max(divisions)
    else:
        division = 10                
    return(division)

def sequence_params_dicter(type, notestepcount, notesteplen):
    div_dict = {10:4, 12:8, 14:16}
    notestepcount = notestepcount*div_dict[notesteplen]
    if type == 'MIDI':
        dispmode = '2'
    else:
        dispmode = '1'
    possible_divisions = [1, 2, 4, 8, 16]
    quantsizes = {16:1, 8:2, 4:4, 2:6, 1:8}
    for i in possible_divisions:
        if not notestepcount%i:
            quantsize = quantsizes[i] 

    params = {'notesteplen': str(notesteplen), 'notestepcount': str(notestepcount), 'dutycyc': '1000', 'midioutchan': '0', 'quantsize': str(quantsize), 'padnote': '0', 'dispmode': dispmode, 'seqplayenable': '0'}
    #notesteplen --> 0 = 8, 1 = 4, 2 = 2, 3 = 1, 4 = 1/2, 6 = 1/4, 8 = 1/8, 10 = 1/16, 12 = 1/32, 14 = 1/64
    #notestepcount --> CHECK
    #dutycyc --> leave
    #midioutchan --> for midi channel set to 1? or 7?
    #quantsize --> Do something with if steps not equal 16/32 etc
    #padnote --> channel?
    #dispmode --> leave
    #seqplayenable --> leave

    #while loop with start and duration to determine division
    #from ableton, extract clip length

    return(params)

def sequence_step_dicter(step_info, track, type, division):
    div_dict = {10:4, 12:8, 14:16}
    division = div_dict[division]
    if type == 'MIDI':
        chan = 256
    else:
        chan = int(track) + 255
    step = round(float(step_info['Start'])*division)
    strtks = step*960
    length = round(float(step_info['Duration'])*division)
    lentks = length*960
    pitch = step_info['Note']
    seqevent = {'step': str(step), 'chan': str(chan), 'type': 'note', 'strtks': str(strtks), 'pitch': str(pitch), 'lencount': str(length), 'lentks': str(lentks)}
    if step_info['Velocity'] != '100':
        seqevent['velocity'] = step_info['Velocity']
    return(seqevent)

def empty_sequence():
    params = {'notesteplen': '10', 'notestepcount': '16', 'dutycyc': '1000', 'midioutchan': '0', 'quantsize': '1', 'padnote': '0', 'dispmode': '1', 'seqplayenable': '0', 'seqstepmode': '1'}
    return(params)

def make_sequences(root, from_ableton):
    #print(from_ableton)
    session = root.find('session')
    current_track = 0
    for track in from_ableton:
        #print('Track', track['Track'])
        #print('   ', 'Track type:', track['Type'])
        for i in range(len(track['Sequences'])):
            row, column = row_column(current_track)
            cell = ET.SubElement(session, 'cell')
            cell.attrib = {'row':str(row), 'column':str(column), 'layer':'1', 'type':'noteseq'}
            params = ET.SubElement(cell, 'params')
            division = find_division(track['Sequences'][i][1])
            params.attrib = sequence_params_dicter(track['Type'], round(track['Sequences'][i][0]), division)
            sequence = ET.SubElement(cell, 'sequence')
            #print('      ', 'Sequence', i+1, ', length:', track['Sequences'][i][0]*4)
            for step in track['Sequences'][i][1]:
                seqevent = ET.SubElement(sequence, 'seqevent')
                seqevent.attrib = sequence_step_dicter(step, track['Track'], track['Type'], division)
            current_track += 1

    for i in range(current_track,20):
        row, column = row_column(i)
        cell = ET.SubElement(session, 'cell')
        cell.attrib = {'row':str(row), 'column':str(column), 'layer':'1', 'type':'noteseq'}
        params = ET.SubElement(cell, 'params')
        params.attrib = empty_sequence()
        sequence = ET.SubElement(cell, 'sequence')
    return(root)    

def make_song(root):
    session = root.find('session')
    for i in range(16):
        cell = ET.SubElement(session, 'cell')
        cell.attrib = {'row':str(i), 'column':'0', 'layer':'2', 'name':'', 'type':'section'}
        params = ET.SubElement(cell, 'params')
        params.attrib = {'sectionlenbars':'8'}
        sequence = ET.SubElement(cell, 'sequence')
    return(root)
   
def make_fx(root):
    session = root.find('session')

    cell = ET.SubElement(session, 'cell')
    cell.attrib = {'row':'0', 'layer':'3', 'type':'delay'}
    params = ET.SubElement(cell, 'params')
    params.attrib = {'delay': '400', 'delaymustime': '6', 'feedback': '400', 'cutoff': '120', 'filtquality': '1000', 'dealybeatsync': '1', 'filtenable': '1', 'delaypingpong': '1'}

    cell = ET.SubElement(session, 'cell')
    cell.attrib = {'row':'1', 'layer':'3', 'type':'reverb'}
    params = ET.SubElement(cell, 'params')
    params.attrib = {'decay': '600', 'predelay': '40', 'damping': '500'}

    cell = ET.SubElement(session, 'cell')
    cell.attrib = {'row':'2', 'layer':'3', 'type':'eq'}
    params = ET.SubElement(cell, 'params')
    params.attrib = {'eqactband': '0', 'eqgain': '0', 'eqcutoff': '200', 'eqres': '400', 'eqenable': '1', 'eqtype': '0', 
                     'eqgain2': '0', 'eqcutoff2': '400', 'eqres2': '400', 'eqenable2': '1', 'eqtype2': '0', 'eqgain3': '0', 
                     'eqcutoff3': '600', 'eqres3': '400', 'eqenable3': '1', 'eqtype3': '0', 'eqgain4': '0', 'eqcutoff4': '800', 
                     'eqres4': '400', 'eqenable4': '1', 'eqtype4': '0'}

    cell = ET.SubElement(session, 'cell')
    cell.attrib = {'row':'4', 'layer':'3', 'type':'null'}
    params = ET.SubElement(cell, 'params')

    return(root)

def make_master(root, tempo):
    session = root.find('session')
    
    cell = ET.SubElement(session, 'cell')
    cell.attrib = {'type':'song'}
    params = ET.SubElement(cell, 'params')
    params.attrib = {'globtempo': str(tempo), 'songmode': '0', 'sectcount': '1', 'sectloop': '1', 'swing': '50', 'keymode': '1', 'keyroot': '3'}

    return(root)

def make_assets(root, assets):
    if len(assets['filepath'])>0:
        session = root.find('session')
        for i in range(len(assets['filepath'])):
            filepath = assets['filepath'][i].split('/')[-1].split('_')[0]
            filename = '.\\' + filepath + '\\' + assets['filepath'][i].split('/')[-1]
            cell = ET.SubElement(session, 'cell')
            cell.attrib = {'row':str(i), 'filename':filename, 'type':'asset'}
            params = ET.SubElement(cell, 'params')
            params.attrib = {'rootnote': str(assets['rootkey'][i]), 'keyrangebottom':str(assets['keyrangemin'][i]), 'keyrangetop':str(assets['keyrangemax'][i]),
                             'velrangebottom':'0', 'velrangetop':'0', 'asssrcrow':str(assets['row'][i]), 'asssrccol':str(assets['column'][i])}

            #asssrcrow
            #asssrccol
    return(root)

def save_xml(root, preset_filepath):
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(preset_filepath, encoding="utf-8", xml_declaration=True)

def decrypt_params(test):
    #print(test)
    test = test.split('<params')[1]
    #print(test)
    test = test.split('/>')[0]
    #print(test)
    test = test.split('"')[0:-1]
    string_dict = {}
    #print(test)
    for i in range(0, len(test),2):
        name = test[i][1:-1]
        string_dict[name] = test[i+1]
    print(string_dict)

def main(args):
    print('Running')
    root = read_project(args.Input)
    tracks, tempo = track_tempo_extractor(root)
    print('The project tempo is:', tempo, 'bpm')
    params, sequences, clips = track_iterator(tracks)
    print('________________\n')
    
    root, assets, clip_samples = make_pads(params, clips, tempo)
    root = make_sequences(root, sequences)
    root = make_song(root)
    root = make_fx(root)
    root = make_assets(root, assets)
    root = make_master(root, tempo)
    preset_filepath = make_output(args.Output, params, args.Manual, clip_samples)
    save_xml(root, preset_filepath)
    
    #decrypt_params('<params gaindb="0" pitch="0" panpos="0" samtrigtype="1" loopmode="1" loopmodes="0" midimode="0" midioutchan="0" reverse="0" cellmode="0" envattack="0" envdecay="200" envsus="1000" envrel="0" samstart="0" samlen="1382400" loopstart="0" loopend="1382400" quantsize="3" synctype="5" actslice="1" outputbus="1" polymode="3" polymodeslice="0" slicestepmode="0" chokegrp="0" dualfilcutoff="0" res="500" rootnote="0" beatcount="48" fx1send="0" fx2send="0" multisammode="0" interpqual="0" playthru="0" slicerquantsize="13" slicersync="0" padnote="0" loopfadeamt="0" lfowave="0" lforate="100" lfoamount="1000" lfokeytrig="0" lfobeatsync="0" lforatebeatsync="0" grainsizeperc="300" grainscat="0" grainpanrnd="0" graindensity="600" slicemode="0" legatomode="0" gainssrcwin="0" grainreadspeed="1000" recpresetlen="0" recquant="3" recinput="0" recinputmulti="0" recusethres="0" recthresh="-20000" recmonoutbus="0" />')

if __name__ == '__main__':
    prog = "Ableton-->BB converter"
    description = """Version 0.2, author Maximilian Karlander \n
    Convert an Ableton Live project to a 1010music Blackbox project
    """
    epilog = "I did good, didn't I?"
    parser = argparse.ArgumentParser(prog=prog, 
                                     description=description, 
                                     epilog=epilog,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument("-i", "--Input", help="Ableton live project input", type=str)
    parser.add_argument("-o", "--Output", help="BB project name and location", type=str)
    parser.add_argument("-m", "--Manual", help="Manual sample extraction", action='store_true')
    args = parser.parse_args()  
    main(args)