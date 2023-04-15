import xml.etree.ElementTree as ET
import subprocess
import argparse
import os

# Configuración del logger
# logging.basicConfig(level=logging.DEBUG)

# Obtener la URL del archivo ISM manifest como argumento de línea de comandos
parser = argparse.ArgumentParser(description='Descarga un video protegido por PlayReady.')
parser.add_argument('url', metavar='URL', type=str, help='URL del archivo ISM manifest')
args = parser.parse_args()

# Descargar el archivo de video con Aria2
nombre_video = os.path.basename(args.url)
subprocess.run(['aria2c', args.url, '-o', nombre_video, '--out', nombre_video, '--allow-overwrite=true'])

# Comprobar si el archivo .ism está disponible
archivo_manifest = 'manifest'
if not os.path.isfile(archivo_manifest):
    # Generar el archivo .ism con mp4split
    subprocess.run(['mp4split', nombre_video, '--ism'])

# Analizar el archivo manifest con ElementTree
tree = ET.parse(archivo_manifest)
root = tree.getroot()

# Definir función para ordenar las resoluciones por tamaño de archivo
def ordenar_resoluciones(resolucion):
    for child in root:
        if child.tag == 'StreamIndex':
            if child.attrib['Type'] == 'video':
                for fragmento in child:
                    if (fragmento.get('MaxWidth', '0') + 'x' + fragmento.get('MaxHeight', '0')) == resolucion:
                        return int(fragmento.get('Size', 0))
    return 0

# Mostrar las resoluciones disponibles para el video ordenadas por tamaño de archivo
resoluciones_video = []
for child in root:
    if child.tag == 'StreamIndex':
        if child.attrib['Type'] == 'video':
            for fragmento in child:
                resolucion = fragmento.get('MaxWidth', '0') + 'x' + fragmento.get('MaxHeight', '0')
                if resolucion not in resoluciones_video and resolucion != '0x0':
                    resoluciones_video.append(resolucion)

resoluciones_formato = []
for i, resolucion in enumerate(sorted(resoluciones_video, key=ordenar_resoluciones, reverse=True)):
    es_hdr = False
    codec = ''
    bitrate = ''
    for child in root:
        if child.tag == 'StreamIndex':
            if child.attrib['Type'] == 'video':
                for fragmento in child:
                    if (fragmento.get('MaxWidth', '0') + 'x' + fragmento.get('MaxHeight', '0')) == resolucion:
                        codec = fragmento.get('FourCC', '')
                        bitrate = fragmento.get('Bitrate', '')
                        if codec in ['hev1']:
                            es_hdr = True
    resolucion_string = str(i+1) + '. ' + resolucion
    if es_hdr:
        resolucion_string += ' - HDR: true'
    else:
        resolucion_string += ' - HDR: false'
    if codec != '':
        resolucion_string += ' - Codec: ' + codec
    if bitrate != '':
        resolucion_string += ' - Bitrate: ' + bitrate + ' kbps'
    resoluciones_formato.append(resolucion_string)

print('Resoluciones disponibles para el video:')
for resolucion in resoluciones_formato:
    print(resolucion)

# Obtener información de los canales de audio
canales_audio = []
for child in root:
    if child.tag == 'StreamIndex':
        if child.attrib['Type'] == 'audio':
            lang_list = []
            for fragmento in child:
                codec = fragmento.get('FourCC', '')
                bitrate = fragmento.get('Bitrate', '')
                lang = fragmento.get('Language', '')
                if codec not in canales_audio and bitrate != '':
                    canales_audio.append(codec)
                    bitrate_kbps = int(bitrate) // 1000
                    for l in lang.split(','):
                        lang_list.append(l.strip())
                    canal_audio_string = str(len(canales_audio)) + '. Codec: ' + codec + ' - Bitrate: ' + str(bitrate_kbps) + ' kbps'
                    print(canal_audio_string)

# Eliminar el archivo .ism
os.remove(archivo_manifest)