from openfhe import *

def create_crypto_context():
    parameters = CCParamsBGVRNS()
    parameters.SetPlaintextModulus(65537)
    parameters.SetMultipartyMode(NOISE_FLOODING_MULTIPARTY)

    cc = GenCryptoContext(parameters)
    cc.Enable(PKE)
    cc.Enable(KEYSWITCH)
    cc.Enable(LEVELEDSHE)
    cc.Enable(ADVANCEDSHE)

    return cc

crypto_context = create_crypto_context()