from web3 import Web3

# 이더리움 네트워크와 상호작용하기 위한 Web3 인스턴스 생성
w3 = Web3(Web3.HTTPProvider('https://your.ethereum.node'))

def send_transaction(private_key, to_address, value):
    """
    주어진 개인 키로 이더리움 트랜잭션을 전송합니다.
    
    :param private_key: 트랜잭션을 서명할 개인 키
    :param to_address: 이더를 보낼 주소
    :param value: 전송할 이더의 양 (Wei 단위)
    :return: 트랜잭션 해시
    """
    account = w3.eth.account.from_key(private_key)
    nonce = w3.eth.getTransactionCount(account.address)

    transaction = {
        'to': to_address,
        'value': value,
        'gas': 2000000,
        'gasPrice': w3.toWei('50', 'gwei'),
        'nonce': nonce,
        'chainId': 1  # 메인넷
    }

    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    return txn_hash.hex()

def interact_with_contract(contract_address, abi, function_name, *args):
    """
    스마트 계약과 상호작용합니다.
    
    :param contract_address: 스마트 계약 주소
    :param abi: 스마트 계약의 ABI
    :param function_name: 호출할 함수의 이름
    :param args: 함수에 전달할 인수
    :return: 함수 호출 결과
    """
    contract = w3.eth.contract(address=contract_address, abi=abi)
    function = contract.functions[function_name](*args)
    return function.call()  # 상태 변경이 없는 함수 호출
