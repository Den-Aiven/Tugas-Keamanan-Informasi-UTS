from PIL import Image
import numpy as np
import random

# =========================
# VIGENERE CIPHER
# =========================
def encrypt_vigenere(plaintext, key):
    result = ""
    key = key.lower()
    for i, char in enumerate(plaintext):
        if char.isalpha():
            shift = ord(key[i % len(key)]) - ord('a')
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char
    return result

def decrypt_vigenere(ciphertext, key):
    result = ""
    key = key.lower()
    for i, char in enumerate(ciphertext):
        if char.isalpha():
            shift = ord(key[i % len(key)]) - ord('a')
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base - shift) % 26 + base)
        else:
            result += char
    return result

# =========================
# KONVERSI
# =========================
def text_to_binary(text):
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

# =========================
# STEGANOGRAFI RANDOM LSB
# =========================
def encode_image(image_path, secret_text, output_path, key):
    img = Image.open(image_path)
    binary_text = text_to_binary(secret_text) + '1111111111111110'

    pixels = list(img.getdata())
    pixels = [list(p) for p in pixels]

    random.seed(key)
    positions = list(range(len(pixels)))
    random.shuffle(positions)

    data_index = 0
    for pos in positions:
        for i in range(3):
            if data_index < len(binary_text):
                pixels[pos][i] = (pixels[pos][i] & ~1) | int(binary_text[data_index])
                data_index += 1

    img.putdata([tuple(p) for p in pixels])
    img.save(output_path)

def decode_image(image_path, key):
    img = Image.open(image_path)
    pixels = list(img.getdata())

    random.seed(key)
    positions = list(range(len(pixels)))
    random.shuffle(positions)

    binary_data = ""
    for pos in positions:
        for i in range(3):
            binary_data += str(pixels[pos][i] & 1)

    delimiter = '1111111111111110'
    end = binary_data.find(delimiter)

    return binary_to_text(binary_data[:end])

# =========================
# PSNR
# =========================
def calculate_psnr(img1_path, img2_path):
    img1 = np.array(Image.open(img1_path), dtype=np.float64)
    img2 = np.array(Image.open(img2_path), dtype=np.float64)

    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return 100

    psnr = 10 * np.log10((255 ** 2) / mse)
    return psnr

# =========================
# MAIN PROGRAM
# =========================
if __name__ == "__main__":
    print("=== HYBRID KRIPTOGRAFI & STEGANOGRAFI ===")

    pesan = input("Masukkan pesan: ")
    key = input("Masukkan key: ")
    gambar_input = input("Masukkan nama gambar (contoh: input.png): ")

    gambar_output = "output.png"

    # ENKRIPSI
    cipher = encrypt_vigenere(pesan, key)
    print("\nCiphertext:", cipher)

    # ENCODE
    encode_image(gambar_input, cipher, gambar_output, key)
    print("Pesan berhasil disisipkan ke gambar!")

    # DECODE
    extracted = decode_image(gambar_output, key)
    print("\nCipher hasil ekstraksi:", extracted)

    # DEKRIPSI
    original = decrypt_vigenere(extracted, key)
    print("Pesan asli:", original)

    # PSNR
    psnr = calculate_psnr(gambar_input, gambar_output)
    print("\nNilai PSNR:", psnr)
