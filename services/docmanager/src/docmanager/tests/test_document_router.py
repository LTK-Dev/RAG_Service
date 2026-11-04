import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import io

# Import models/classes
from postgres.schemas import DocumentSchema, DocumentStatus
from docmanager import app
from docmanager.application.createDocument import CreateDocumentAppService
from docmanager.application.getDocument import GetDocumentsAppService
from docmanager.application.createDocument import CreateDocumentAppService
from docmanager.api.schemas import DocumentResponse
from docmanager.shared.exceptions import DatabaseError


@pytest.fixture
def client(monkeypatch):
    """
    Tạo một TestClient và mock (giả lập) các kết nối bên ngoài (DB, Minio)
    mà lifespan cố gắng khởi tạo.
    """

    # 1. Mock 'SQLDatabase' (từ postgres_lib)
    mock_db = MagicMock()
    mock_db.close_engine.return_value = None
    # (Chúng ta sẽ mock các hàm cụ thể như 'get_documents' trong từng test)

    # 2. Mock 'MinioService' (từ minio_lib)
    mock_minio = MagicMock()

    # 3. Dùng monkeypatch để "chặn" (intercept) hàm __init__ của chúng
    #    và thay thế chúng bằng các đối tượng mock
    with patch('libs.postgres.src.postgres.SQLDatabase', return_value=mock_db):
        with patch('libs.storage.src.storage.MinioService', return_value=mock_minio):

            # Gán mock vào app.state (giống hệt cách lifespan làm)
            app.state.sql_database = mock_db
            app.state.minio_service = mock_minio

            # Yield (cung cấp) client cho test
            yield TestClient(app)


# --- Dữ liệu giả (Mock Data) ---
MOCK_DOCUMENTS_LIST = [
    DocumentSchema(
        id=1,
        file_name='t1.pdf',
        minio_path='/f',
        status=DocumentStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
    ),
    DocumentSchema(
        id=2,
        file_name='t2.docx',
        minio_path='/f',
        status=DocumentStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    ),
]

MOCK_NEW_DOCUMENT = DocumentSchema(
    id=3,
    file_name='new_file.pdf',
    minio_path='<uuid>-new_file.pdf',
    status=DocumentStatus.PENDING,
    created_at=datetime.now(timezone.utc),
)

# === Test cho GET /documents (PR 1) ===


def test_get_documents_success(client):
    """
    Test F1: GET /documents (thành công)
    """
    # 1. Mock lớp Application trả về MOCK_ITEMS
    with patch.object(
        GetDocumentsAppService, 'get_documents', return_value=MOCK_DOCUMENTS_LIST,
    ) as mock_get_docs:

        # 2. Gọi API
        response = client.get('/api/v1/documents', params={'limit': 10})

    # 3. Kiểm tra
    assert response.status_code == 200
    mock_get_docs.assert_called_once_with(
        status=None, order_by='created_at:desc', limit=10,  # Giá trị mặc định
    )
    res_data = response.json()
    assert len(res_data) == 2
    assert res_data[0]['file_name'] == 't1.pdf'


def test_get_documents_error(client):
    """
    Test F1: GET /documents (lỗi 500)
    """
    # 1. Mock lớp Application ném ra lỗi DB
    with patch.object(
        GetDocumentsAppService,
        'get_documents',
        side_effect=DatabaseError('DB query failed'),
    ):
        # 2. Gọi API
        response = client.get('/api/v1/documents')

    # 3. Kiểm tra
    assert response.status_code == 500


# === Test cho POST /documents (PR 2.1) ===


def test_create_document_success(client):
    """
    Test F2: POST /documents (thành công)
    """
    # 1. Chuẩn bị file giả để upload
    fake_file_content = b'This is a fake pdf file.'
    fake_file = io.BytesIO(fake_file_content)
    fake_file.name = 'new_file.pdf'

    # 2. Mock lớp Application trả về document mới
    with patch.object(
        CreateDocumentAppService, 'process', return_value=MOCK_NEW_DOCUMENT,
    ) as mock_create_doc:

        # 3. Gọi API (dùng 'files=')
        response = client.post(
            '/api/v1/documents',
            files={'file': (fake_file.name, fake_file, 'application/pdf')},
        )

    # 4. Kiểm tra
    assert response.status_code == 201  # (201 Created)
    assert response.json()['file_name'] == 'new_file.pdf'
    assert response.json()['status'] == 'PENDING'

    # Kiểm tra xem mock_create_doc có được gọi với đối tượng UploadFile không
    mock_create_doc.assert_called_once()
    assert mock_create_doc.call_args[1]['upload_file'].filename == 'new_file.pdf'


def test_create_document_no_file(client):
    """
    Test F2: POST /documents (thiếu file)
    """
    # 1. Gọi API (không có 'files=')
    response = client.post('/api/v1/documents')

    # 2. Kiểm tra
    # FastAPI tự động trả về 422 (Unprocessable Entity)
    assert response.status_code == 422
    assert 'Field required' in response.json()['detail'][0]['msg']
