# Ableton Live .als to 1010music Blackbox .xml converter
## What it does
This script attempts to convert an Ableton Live `.als` project file to a 1010music Blackbox readable `.xml` file.
What it currently does is the following:
- Extract Simpler settings
- Extract Sampler settings
- Extract clip sequences from Simpler and Sampler tracks, along with clip sequences from Ableton Analog tracks and assign these as MIDI sequences on the Blackbox
- Extract audio clips as loop pads as loop pads on the Blackbox

For Simpler and Sampler the following settings are extracted and converted:
- Play start and end (loop is ignored)
- ADSR settings (the coefficients used here could use some tweaking)
- Multisample mappings
As a note it won’t handle grouped Simplers/Samplers but expect it to be a standalone instrument.

For sequences the following things are extracted and converted:
- Each step
- Division is assumed to be 1/16, however if 1/32 or 1/64 note lengths are identified this will be used
- Sequence length
- Assigned to its corresponding Simpler/Sampler/MIDI track 
For Audio clip tracks the following things are extracted:
- Number of beats

For Simpler/Sampler/Audio tracks all necessary samples are copied to a specified project folder where the preset file is also saved. All sample references in the preset files are referring here, so by copying the whole folder to the Blackbox preset folder all samples will tag along. Samples need to be in .wav format though.

## Limitations
A significant limitation at the moment is that I’m working in Live 10 and I’m on Blackbox 2.1.5 so all of this was written based on this and function is not guaranteed for other versions. I’ve also only tested this on Mac (albeit two different ones). All code is written in Python and I’ve only used standard packages.

## How to run the script
1. First, you need to have python 3 installed. I've used python 3.9.7 when writing the script. Apart from that I believe all packages used are standard python packages. 
2. Download the script in the `code` folder called `xml_read.py.`
3. In terminal, cd your way to where the script is located and type `python3 xml_read.py -h`. This will show you the three arguments:
    - `-i` or `--Input` is your `.als` file
    - `-o` or `--Output` is what you want your Blackbox project to be called and located.
    - `-m` or `--Manual` is an option that will not copy any of the samples identified. This is convenient if you for example are converting a project made on another computer and the filepaths to all the files are incorrect. You will than have to manually copy all the sounds to you project root folder.
4. Run the script with the appropriate settings.
5. Copy the project folder to your Blackbox.
Note that samples have to be `.wav` files.

## Requests and roadmap
- Nothing to show here atm but things will probably change.

## Change log
- 2023-05-11 initiated version 0.2 on github


## Contact
If you have any questions or feature requests, please contact me (pro424) on the 1010music forum or write in the [thread](https://forum.1010music.com/forum/products/blackbox/support-blackbox/43727-python-script-converting-an-ableton-live-project-to-blackbox-xml)
Be warned though that I have limited time and programming experience and do not take any responisbility for support. 