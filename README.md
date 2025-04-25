# echomatrix


Voice-driven AI IVR system using, OpenAI APIs. No midleman (freepbx/asterisk)

## 🔧 Features

- Whisper for speech-to-text
- GPT-4 Turbo for smart responses
- OpenAI TTS for fast, high-quality voice replies
- Modular Python design with AGI integration

## 🚀 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt

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