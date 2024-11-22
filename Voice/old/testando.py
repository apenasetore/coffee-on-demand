import speech_recognition as sr
import os
import sys
import logging

logging.basicConfig(level=logging.ERROR)  # Mostra apenas erros críticos

# Inicializa o reconhecedor
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Lista para armazenar os dados dos áudios
audio_data_list = []

print("Ajustando ao ruído ambiente... Aguarde.")
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)  # Ajusta ao ruído ambiente
    recognizer.energy_threshold = 4000  # Ajusta o nível de ruído

print("Pronto para detectar fala. Fique à vontade para falar.")

try:
    while True:
        with mic as source:
            print("Aguardando som...")
            # Use timeout e phrase_time_limit para gerenciar o silêncio
            audio = recognizer.listen(
                source,
                timeout=5,  # Tempo máximo para detectar som inicial
                phrase_time_limit=5  # Tempo máximo sem som antes de parar de gravar
            )
            print("Som detectado! Gravando...")
            
            # Armazena o áudio na lista
            audio_data_list.append(audio.get_wav_data())
except sr.WaitTimeoutError:
    print("Nenhum som detectado no tempo limite. Encerrando.")
except KeyboardInterrupt:
    print("Encerrando detecção.")

# Salva todos os áudios acumulados em um único arquivo
if audio_data_list:
    with open("gravacao_final.wav", "wb") as f:
        for audio_data in audio_data_list:
            f.write(audio_data)
    print("Todos os áudios foram salvos em 'gravacao_final.wav'.")
else:
    print("Nenhum áudio foi gravado.")
