from openfhe import *
import requests

def generate_keys():
    parameters = CCParamsBGVRNS()
    parameters.SetPlaintextModulus(65537)
    parameters.SetMultipartyMode(NOISE_FLOODING_MULTIPARTY)

    cc = GenCryptoContext(parameters)
    cc.Enable(PKE)
    cc.Enable(KEYSWITCH)
    cc.Enable(LEVELEDSHE)
    cc.Enable(ADVANCEDSHE)

    sk = cc.KeyGen()
    pk = cc.PublicKey()

    return sk, pk, cc

def encrypt_data(data, pk, cc):
    plaintext = cc.MakeStringPlaintext(data)
    ciphertext = cc.Encrypt(plaintext, pk)
    return ciphertext

def send_to_backend(ciphertext):
    url = "http://localhost:5000/api/encrypt"  # 백엔드 API 엔드포인트
    response = requests.post(url, json={'ciphertext': ciphertext})
    return response.json()

if __name__ == "__main__":
    sk, pk, cc = generate_keys()
    data = input("암호화할 데이터를 입력하세요: ")
    ciphertext = encrypt_data(data, pk, cc)
    response = send_to_backend(ciphertext)
    print("서버 응답:", response)