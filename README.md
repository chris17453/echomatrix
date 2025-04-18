# echomatrix


Voice-driven AI IVR system using FreePBX, Asterisk, and OpenAI APIs.

## 🔧 Features

- Whisper for speech-to-text
- GPT-4 Turbo for smart responses
- OpenAI TTS for fast, high-quality voice replies
- Modular Python design with AGI integration

## 🚀 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt

## NONE OF THIS1

sudo dnf install mpg123  alsa-utils 
# you need to install sox. IT might requre a build from scratch and you need a lot of dependencies to get mp3 etcv working.

wget    https://cytranet-dal.dl.sourceforge.net/project/sox/sox/14.4.2/sox-14.4.2.tar.bz2
tar -xvjf sox-14.4.2.tar.bz2 sox-14.4.2/
cd sox-14.4.2/
dnf install  'lame'* 'flac*' 'libsox*'
dnf install opencore-amr-devel libid3tag-devel libmad-devel twolame-devel \
            libvorbis-devel opus-devel libsndfile-devel wavpack-devel file-devel libpng-devel
  
# you need to add #include <math.h> to this file on line 23
vi src/sox_sample_test.h

./configure
make -s && make install
```

## PJSUA2 Build/Install
So you need to build the pjusa2 project.. then compile the python swig stuff...
```bash
# clone the repo
git clone https://github.com/pjsip/pjproject.git

# build the base library
cd pjproject
export CFLAGS="-fPIC"
export CXXFLAGS="-fPIC"
./configure
make dep
make


# make the python module (This doent put it in your pipenv)
cd pjsip-apps/src/swig/python
make
make install


# install in yourr project
cd /web/echomatrix
pipenv run pip install ../pjproject/pjsip-apps/src/swig/python
```