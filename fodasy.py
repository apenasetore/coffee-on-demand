import pyaudio

CHUNK_DURATION_MS = 30
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK =  int(RATE * CHUNK_DURATION_MS / 1000)

# Inicializa o PyAudio
p = pyaudio.PyAudio()

# Verifica as taxas de amostragem disponíveis
info = p.get_host_api_info_by_index(0)
num_devices = info.get('deviceCount')

for i in range(0, num_devices):
    device_info = p.get_device_info_by_index(i)
    print(f"Dispositivo {i}: {device_info}")
    print(f"Taxas de amostragem suportadas: {device_info.get('defaultSampleRate')}")



# Fechar
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK,input_device_index=1)
p.terminate()