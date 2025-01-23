# my-python-project/README.md

# My Python Project

이 프로젝트는 OpenFHE 라이브러리와 Web3 라이브러리를 활용하여 백엔드와 프론트엔드가 통합된 애플리케이션을 구현합니다. 이 애플리케이션은 이더리움 네트워크와 상호작용하며, 암호화된 데이터를 안전하게 전송할 수 있는 기능을 제공합니다.

## 프로젝트 구조

```
my-python-project
├── backend
│   ├── app.py               # 백엔드 애플리케이션의 진입점
│   ├── eth_interaction.py    # 이더리움 네트워크와 상호작용하는 기능
│   ├── requirements.txt      # 백엔드 의존성 목록
│   └── README.md             # 백엔드 관련 문서
├── frontend
│   ├── main.py               # 프론트엔드 애플리케이션의 진입점
│   ├── keygen_encrypt.py      # 키 생성 및 암호화 기능
│   ├── requirements.txt      # 프론트엔드 의존성 목록
│   └── README.md             # 프론트엔드 관련 문서
├── shared
│   ├── crypto_context.py      # 공유 CryptoContext 객체 정의
│   └── README.md             # 공유 컴포넌트 관련 문서
└── README.md                 # 전체 프로젝트 문서
```

## 설치 및 실행

1. **의존성 설치**
   - 백엔드와 프론트엔드 디렉토리 내의 `requirements.txt` 파일을 사용하여 필요한 패키지를 설치합니다.
   - 예: `pip install -r backend/requirements.txt`
   - 예: `pip install -r frontend/requirements.txt`

2. **백엔드 실행**
   - `backend/app.py` 파일을 실행하여 웹 서버를 시작합니다.
   - 예: `python backend/app.py`

3. **프론트엔드 실행**
   - `frontend/main.py` 파일을 실행하여 프론트엔드 애플리케이션을 시작합니다.
   - 예: `python frontend/main.py`

## 사용 방법

- 프론트엔드에서 사용자 입력을 통해 키를 생성하고 데이터를 암호화한 후, 이를 백엔드로 전송합니다.
- 백엔드는 수신한 암호문을 처리하고 이더리움 네트워크와 상호작용합니다.

## 기여

기여를 원하시는 분은 이 저장소를 포크한 후, 변경 사항을 제안해 주세요.# -
