# Makefile for AUDIO_MANAGER voice registration
# Usage: make voices CONFIG=path/to/config.yaml

# Default config path if not specified
CONFIG ?= --config ../audio_manager.yaml
AUDIO_MANAGER=python -m audio_manager

.PHONY: voices standard-voices hd-voices

# Register all voices
voices: standard-voices hd-voices

# Standard voices (tts-1 model)
standard-voices:
	@echo "Registering standard voices (tts-1 model)..."
	@echo "--------------------------------------------"
	
	@echo "Registering Alloy voice (neutral)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1" --voice "alloy" --provider "openai" \
		--instruction ""
	
	@echo "Registering Echo voice (male)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1" --voice "echo" --provider "openai" \
		--instruction ""
	
	@echo "Registering Fable voice (male)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1" --voice "fable" --provider "openai" \
		--instruction ""
	
	@echo "Registering Onyx voice (male)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1" --voice "onyx" --provider "openai" \
		--instruction ""
	
	@echo "Registering Nova voice (female)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1" --voice "nova" --provider "openai" \
		--instruction ""
	
	@echo "Registering Shimmer voice (female)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1" --voice "shimmer" --provider "openai" \
		--instruction ""

# High-definition voices (tts-1-hd model)
hd-voices:
	@echo "Registering high-definition voices (tts-1-hd model)..."
	@echo "-----------------------------------------------------"
	
	@echo "Registering HD Alloy voice (neutral)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1-hd" --voice "alloy" --provider "openai" \
		--instruction ""
	
	@echo "Registering HD Echo voice (male)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1-hd" --voice "echo" --provider "openai" \
		--instruction ""
	
	@echo "Registering HD Fable voice (male)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1-hd" --voice "fable" --provider "openai" \
		--instruction ""
	
	@echo "Registering HD Onyx voice (male)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1-hd" --voice "onyx" --provider "openai" \
		--instruction ""
	
	@echo "Registering HD Nova voice (female)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1-hd" --voice "nova" --provider "openai" \
		--instruction ""
	
	@echo "Registering HD Shimmer voice (female)"
	${AUDIO_MANAGER} $(CONFIG) ai register --model "tts-1-hd" --voice "shimmer" --provider "openai" \
		--instruction ""

# List all registered voices
list-voices:
	@echo "Listing all registered voices..."
	${AUDIO_MANAGER} $(CONFIG) ai list


generate-default-speech:
 	python -m audio_manager --config ../audio_manager.yaml  tts generate "Welcome to Watkins Labs"

list-recordings:
 	python -m audio_manager --config ../audio_manager.yaml  recordings list

get-recording:
	python -m audio_manager --config ../audio_manager.yaml  recordings find-by-ai-text --text "Welcome to Watkins Labs" --ai-identity-id 1