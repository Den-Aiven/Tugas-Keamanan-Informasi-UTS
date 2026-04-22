import streamlit as st
import numpy as np
from PIL import Image
import cv2
import random
from skimage.metrics import structural_similarity as ssim
import math
import io
import hashlib

# =============================
# 🎨 CUSTOM UI
# =============================
st.set_page_config(page_title="Crypto-Stego App", layout="wide")

st.markdown("""
<style>
.main {
    background-color: #0e1117;
}
h1, h2, h3 {
    text-align: center;
}
.block-container {
    padding-top: 2rem;
}
.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3em;
}
</style>
""", unsafe_allow_html=True)

st.title("🔐 Hybrid Crypto-Steganography")
st.caption("Vigenere Cipher + Adaptive LSB (Edge + Random)")

st.warning("⚠️ Gunakan format PNG! JPG akan merusak data steganografi.")

# =============================
# 🔑 SEED (FIX)
# =============================
def get_seed(key):
    return int(hashlib.sha256(key.encode()).hexdigest(), 16)

# =============================
# 🔐 VIGENERE
# =============================
def vigenere_encrypt(text, key):
    result = ""
    key = key.lower()
    key_index = 0

    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - 97
            base = 65 if char.isupper() else 97
            result += chr((ord(char) - base + shift) % 26 + base)
            key_index += 1
        else:
            result += char
    return result

def vigenere_decrypt(cipher, key):
    result = ""
    key = key.lower()
    key_index = 0

    for char in cipher:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - 97
            base = 65 if char.isupper() else 97
            result += chr((ord(char) - base - shift) % 26 + base)
            key_index += 1
        else:
            result += char
    return result

# =============================
# EDGE (FIX STABIL)
# =============================
def get_edge_positions(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # blur biar stabil
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    
    edges = cv2.Canny(gray, 50, 150)
    positions = np.argwhere(edges > 0)

    # fallback kalau edge terlalu sedikit
    if len(positions) < 100:
        h, w, _ = image.shape
        positions = np.array([(i, j) for i in range(h) for j in range(w)])

    return positions

# =============================
# EMBED (FIX)
# =============================
def embed_data(image, data, key):
    img = image.copy()

    binary_data = ''.join(format(ord(c), '08b') for c in data)
    data_len = format(len(binary_data), '032b')
    binary_data = data_len + binary_data

    positions = get_edge_positions(img)

    random.seed(get_seed(key))
    random.shuffle(positions)

    max_capacity = len(positions) * 3
    if len(binary_data) > max_capacity:
        raise ValueError("Message too large for this image")

    idx = 0
    for pos in positions:
        i, j = pos
        for k in range(3):
            if idx < len(binary_data):
                img[i, j, k] = (img[i, j, k] & 254) | int(binary_data[idx])
                idx += 1
            else:
                break
        if idx >= len(binary_data):
            break

    return img

# =============================
# EXTRACT (FIX)
# =============================
def extract_data(image, key):
    img = image.copy()
    positions = get_edge_positions(img)

    random.seed(get_seed(key))
    random.shuffle(positions)

    bits = []
    for pos in positions:
        i, j = pos
        for k in range(3):
            bits.append(str(img[i, j, k] & 1))

    bits = ''.join(bits)

    if len(bits) < 32:
        raise ValueError("Invalid image or no hidden data")

    data_len = int(bits[:32], 2)

    if data_len <= 0 or data_len > len(bits):
        raise ValueError("Corrupted data or wrong key")

    data_bits = bits[32:32 + data_len]

    chars = []
    for i in range(0, len(data_bits), 8):
        byte = data_bits[i:i+8]
        if len(byte) == 8:
            chars.append(chr(int(byte, 2)))

    return ''.join(chars)

# =============================
# METRICS
# =============================
def calculate_psnr(original, stego):
    mse = np.mean((original - stego) ** 2)
    if mse == 0:
        return 100
    return 20 * math.log10(255.0 / math.sqrt(mse))

def calculate_ssim(original, stego):
    return ssim(original, stego, channel_axis=2)

# =============================
# MODE SWITCH
# =============================
mode = st.radio("Choose Mode", ["🔐 Embed", "🔓 Extract"], horizontal=True)

# =============================
# EMBED UI
# =============================
if mode == "🔐 Embed":
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("📷 Upload Image", type=["png"])
        message = st.text_area("📝 The text you want to hide")
        key = st.text_input("🔑 Password / Key", type="password")

        process = st.button("🚀 Process")

    with col2:
        if uploaded_file:
            st.image(uploaded_file, caption="Preview Image")

    if process and uploaded_file and message and key:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            img_array = np.array(image)

            cipher = vigenere_encrypt(message, key)
            stego_img = embed_data(img_array, cipher, key)

            psnr_val = calculate_psnr(img_array, stego_img)
            ssim_val = calculate_ssim(img_array, stego_img)

            st.success("✅ Embedding Success")

            st.subheader("🔑 Ciphertext")
            st.code(cipher)

            col1, col2 = st.columns(2)
            with col1:
                st.image(image, caption="Original")
            with col2:
                st.image(stego_img, caption="Stego")

            col1, col2 = st.columns(2)
            col1.metric("PSNR", f"{psnr_val:.2f}")
            col2.metric("SSIM", f"{ssim_val:.4f}")

            buf = io.BytesIO()
            Image.fromarray(stego_img).save(buf, format="PNG")

            st.download_button(
                "⬇️ Download Stego Image",
                buf.getvalue(),
                "stego.png",
                "image/png"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# =============================
# EXTRACT UI
# =============================
if mode == "🔓 Extract":
    uploaded_file = st.file_uploader("📷 Upload Stego Image", type=["png"])
    key = st.text_input("🔑 Password / Key", type="password")

    if uploaded_file:
        st.image(uploaded_file, caption="Stego Preview")

    if st.button("🔍 Extract") and uploaded_file and key:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            img_array = np.array(image)

            cipher = extract_data(img_array, key)
            message = vigenere_decrypt(cipher, key)

            st.success("✅ Extraction Success")

            st.subheader("🔑 Ciphertext")
            st.code(cipher)

            st.subheader("📨 Decrypted Message")
            st.success(message)

        except Exception as e:
            st.error(f"❌ Failed: {str(e)}")
