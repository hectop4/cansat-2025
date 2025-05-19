import serial
import re

def hex_to_decimal(hex_value):
    """Convierte un valor hexadecimal a decimal."""
    try:
        # Eliminar cualquier posible prefijo como "0x" y convertir el valor hexadecimal a decimal
        decimal_value = int(hex_value, 16)
        return decimal_value
    except ValueError:
        return "Valor no válido"

def process_message(message):
    """Extrae y procesa la parte hexadecimal del mensaje, manteniendo la letra junto al valor."""
    # Buscar y extraer la letra y el valor hexadecimal que sigue (por ejemplo, 'P120ae' -> 'P120ae')
    match = re.search(r"([A-Za-z])([0-9a-fA-F]+)", message)  # El patrón busca una letra seguida de números/hex
    if match:
        letter = match.group(1)  # La letra indicativa (ej. 'P')
        hex_value = match.group(2)  # El valor hexadecimal (ej. '120ae')
        return letter, hex_value
    else:
        return None, None

def read_from_serial(serial_port):
    """Lee un mensaje del puerto serial."""
    try:
        message = serial_port.readline().decode('utf-8').strip()  # Leer una línea y decodificarla
        return message
    except:
        return None

def main():
    """Función principal para recibir y procesar los datos desde el puerto serial."""
    print("Esperando datos desde el puerto serial...")
    
    # Configurar el puerto serial (asegúrate de usar el puerto correcto)
    serial_port = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)  # Cambia 'COM3' al puerto de tu dispositivo
    serial_port.flush()

    while True:
        # Leer mensaje desde el serial
        message = read_from_serial(serial_port)
        
        if message:
            print(f"Mensaje recibido: {message}")
            # Procesar el mensaje y extraer la parte hexadecimal
            letter, hex_value = process_message(message)
            
            if hex_value:
                # Convertir el valor hexadecimal a decimal
                decimal_value = hex_to_decimal(hex_value)
                if isinstance(decimal_value, int):  # Verificar si la conversión fue exitosa
                    print(f"{letter}{decimal_value}")  # Mostrar la letra junto al valor decimal
                else:
                    print(f"Error al convertir hexadecimal: {hex_value}")
            else:
                print("No se encontraron valores hexadecimales en el mensaje.")
        else:
            print("No se recibió ningún mensaje. Intentando nuevamente...")

if __name__ == "__main__":
    main()

