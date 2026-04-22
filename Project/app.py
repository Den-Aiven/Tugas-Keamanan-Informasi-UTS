import streamlit as st
from hybrid_stego import *
from PIL import Image
import os

st.title("🔐 Hybrid Crypto-Steganography")

# INPUT
pesan = st.text_input("Masukkan Pesan")
key = st.text_input("Masukkan Key")

uploaded_file = st.file_uploader("Upload Gambar", type=["png", "jpg"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="Gambar Asli", use_column_width=True)

    if st.button("Proses"):
        input_path = "temp_input.png"
        output_path = "temp_output.png"

        img.save(input_path)

        # ENKRIPSI
        cipher = encrypt_vigenere(pesan, key)

        # ENCODE
        encode_image(input_path, cipher, output_path, key)

        # TAMPILKAN HASIL
        stego_img = Image.open(output_path)
        st.image(stego_img, caption="Gambar Stego", use_column_width=True)

        # DECODE
        extracted = decode_image(output_path, key)
        original = decrypt_vigenere(extracted, key)

        st.success(f"Pesan hasil decode: {original}")

        # PSNR
        psnr = calculate_psnr(input_path, output_path)
        st.info(f"Nilai PSNR: {psnr:.2f} dB")
