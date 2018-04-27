import os, sys
import time
import argparse
import re

from pyfluidsynth3 import fluidhandle, fluidsettings, fluidaudiodriver, fluidsynth, fluidmidirouter, fluidmididriver

import shlex, subprocess

def read_config(config_path):
    config = dict()
    with open(config_path, 'r') as f:
        for l in f:
            m = re.match(' *([^\s]+) +([^\s]+)', l)
            if m:
                opt = m.group(1)
                val = m.group(2)
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                        # passing param as string
                config[opt] = val

    return config

def read_patch(patch_path, sf_dir='.'):
    patch = dict()
    sf = 'default.sf2'
    with open(patch_path, 'r') as f:
        for l in f:
            m_sf = re.match('\[(\w+.sf2)\]', l)
            m_prog = re.match('prog +(\d+) +(\d+) +(\d+)', l)
            if m_sf:
                if os.path.isfile(os.path.join(sf_dir, m_sf.group(1))):
                    sf_path = os.path.join(sf_dir, m_sf.group(1))
                else:
                    print("Didn't found SoundFont")
            elif m_prog:
                chan = m_prog.group(1)
                bank = m_prog.group(2)
                prog = m_prog.group(3)
                patch[chan] = (sf_path, int(bank), int(prog))
    return patch

def load_patch(synth, patch_conf):
    sf_list = []
    for chan, conf in patch_conf.items():
        sf, bank, prog = conf
        if sf not in sf_list:
            print("Loading SoundFont: " + sf)
            synth.load_soundfont(sf, reload_presets=False)
            sf_list.append(sf)
        synth.bank_select(int(chan), bank)
        synth.program_change(int(chan), prog)


def get_io_clients(in_clients, out_clients):
    I, O = (-1, -1)
    cmd = ["aconnect", "-i"]
    ilist = subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True).stdout
    for c in in_clients:
        m_client = re.search('(?:client) (\d+): .*' + c + '.*', ilist, re.IGNORECASE + re.MULTILINE)
        if m_client:
            I = m_client.group(1)

    cmd = ["aconnect", "-o"]
    ilist = subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True).stdout
    for c in out_clients:
        m_client = re.search('(?:client) (\d+): .*' + c + '.*', ilist, re.IGNORECASE + re.MULTILINE)
        if m_client:
            O = m_client.group(1)

    return I, O


class PyFluidLive():

    IN_CLIENTS = ['roland', 'yamaha', 'vmpk']
    OUT_CLIENTS = ['fluid']

    def __init__(self, sf_dir, confs_fname='synth', lib_path='/usr/lib/libfluidsynth'):
        self.config = read_config(confs_fname + '.config')
        self.patch = read_patch(confs_fname + '.patch', sf_dir=sf_dir)

        self.handle = fluidhandle.FluidHandle(lib_path)
        self.settings = fluidsettings.FluidSettings(self.handle)
        for opt, value in self.config.items():
            self.settings[opt] = value
        self.synth = fluidsynth.FluidSynth( self.handle, self.settings )
        self.adriver = fluidaudiodriver.FluidAudioDriver(self.handle, self.synth, self.settings)
        self.router = fluidmidirouter.FluidMidiRouter(self.handle, self.settings, self.synth)
        self.mdriver = fluidmididriver.FluidMidiDriver(self.handle, self.settings, self.router)

        self.sf_list = load_patch(self.synth, self.patch)

        self.i_client, self.o_client = get_io_clients(self.IN_CLIENTS, self.OUT_CLIENTS)

        cmd = ["aconnect", self.i_client, self.o_client]
        subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True)


    def __del__(self):
        # cmd = ["aconnect", "-x"]
        # subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True)

        del self.mdriver
        del self.router
        del self.adriver
        del self.synth
        del self.settings
        del self.handle

if __name__ == "__main__":
    LiveSynth = PyFluidLive(sf_dir='../soundfonts')
    print(str(LiveSynth.config))
    print(str(LiveSynth.patch))
    print('I: ' + LiveSynth.i_client + ' / O: ' + LiveSynth.o_client)

    seq = (79, 78, 79, 74, 79, 69, 79, 67, 79, 72, 79, 76,
           79, 78, 79, 74, 79, 69, 79, 67, 79, 72, 79, 76,
           79, 78, 79, 74, 79, 72, 79, 76, 79, 78, 79, 74,
           79, 72, 79, 76, 79, 78, 79, 74, 79, 72, 79, 76,
           79, 76, 74, 71, 69, 67, 69, 67, 64, 67, 64, 62,
           64, 62, 59, 62, 59, 57, 64, 62, 59, 62, 59, 57,
           64, 62, 59, 62, 59, 57, 43)

    for note in seq:
        LiveSynth.synth.noteon(7, note, 1.0)
        time.sleep(0.1)
        LiveSynth.synth.noteoff(7, note)

    time.sleep(10)