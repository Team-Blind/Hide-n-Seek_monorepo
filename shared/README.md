# README for Shared Components

이 디렉토리는 백엔드와 프론트엔드에서 공유되는 구성 요소를 포함하고 있습니다. 주로 암호화 및 복호화에 사용되는 CryptoContext 객체를 정의합니다.

## CryptoContext 사용법

`crypto_context.py` 파일에서 정의된 CryptoContext 객체는 백엔드와 프론트엔드 모두에서 사용됩니다. 이를 통해 동일한 암호화 컨텍스트를 활용하여 데이터의 일관성을 유지할 수 있습니다.

### 설치 및 설정

1. 필요한 라이브러리를 설치합니다.
2. `crypto_context.py` 파일을 임포트하여 CryptoContext 객체를 초기화합니다.
3. 백엔드와 프론트엔드에서 동일한 CryptoContext를 사용하여 암호화 및 복호화를 수행합니다.

이 문서에서는 CryptoContext의 사용법과 설정 방법에 대한 자세한 내용을 다룹니다.