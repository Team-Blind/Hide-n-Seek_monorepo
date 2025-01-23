# /my-python-project/my-python-project/frontend/README.md

# Frontend Application for My Python Project

이 프로젝트의 프론트엔드 애플리케이션은 OpenFHE 라이브러리를 사용하여 키 생성 및 암호화 기능을 제공합니다. 이 문서는 프론트엔드 설정 및 사용 방법에 대한 정보를 포함합니다.

## 프로젝트 구조

- `main.py`: OpenFHE 라이브러리를 초기화하고, 키를 생성하며, 사용자 입력을 처리하는 진입점입니다.
- `keygen_encrypt.py`: OpenFHE 라이브러리를 사용하여 키 생성 및 암호화를 수행하는 함수가 포함되어 있습니다. 생성된 암호문을 백엔드로 전송하는 기능도 포함되어 있습니다.
- `requirements.txt`: 프론트엔드에 필요한 종속성을 나열합니다.

## 설치 및 실행

1. **종속성 설치**: 
   ```bash
   pip install -r requirements.txt
   ```

2. **애플리케이션 실행**:
   ```bash
   python main.py
   ```

## 사용 방법

1. 애플리케이션을 실행하면 사용자 인터페이스가 표시됩니다.
2. 필요한 입력을 제공하고 암호화 버튼을 클릭하여 데이터를 암호화합니다.
3. 생성된 암호문은 백엔드 서버로 전송됩니다.

## 기여

기여를 원하시면 이 저장소를 포크하고 풀 리퀘스트를 제출해 주세요.