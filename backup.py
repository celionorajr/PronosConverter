import sys
import os
import json
import uuid
from PyQt5 import QtWidgets, QtGui, QtCore
from pydicom.dataset import Dataset, FileDataset
from datetime import datetime
from pynetdicom import AE
from pynetdicom.sop_class import CTImageStorage
from PIL import Image
from pydicom.encaps import encapsulate

# Carregar configurações do arquivo config.json
def load_config():
    with open("config.json", "r") as config_file:
        return json.load(config_file)

# Gerar UID compatível com o padrão DICOM
def generate_uid(prefix="1.2.826.0.1.3680043.2.1125"):
    return f"{prefix}.{uuid.uuid4().int >> 64}"

# Converter JPG para DICOM
def convert_to_dicom(jpg_path, patient_name, output_folder, study_uid, series_uid):
    image = Image.open(jpg_path)
    image = image.convert('RGB')  # Garantir que a imagem está em formato RGB
    rows, cols = image.size

    # Criar dataset DICOM
    dataset = Dataset()
    dataset.PatientName = patient_name
    dataset.PatientID = f"ID-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    dataset.StudyDate = datetime.now().strftime('%Y%m%d')
    dataset.StudyTime = datetime.now().strftime('%H%M%S')
    dataset.Modality = "OT"  # Outro
    dataset.Rows = cols
    dataset.Columns = rows
    dataset.SamplesPerPixel = 3  # RGB
    dataset.PhotometricInterpretation = "RGB"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0

    # Encapsular dados da imagem para Transfer Syntax JPEG Lossless
    pixel_data = image.tobytes()
    dataset.PixelData = pixel_data

    # Adicionar UIDs obrigatórios
    dataset.SOPClassUID = CTImageStorage
    dataset.SOPInstanceUID = generate_uid()
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid

    # Configurar Transfer Syntax JPEG Lossless
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = dataset.SOPClassUID
    file_meta.MediaStorageSOPInstanceUID = dataset.SOPInstanceUID
    file_meta.ImplementationClassUID = "1.2.826.0.1.3680043.3.1"
    file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # Implicit VR Little Endian

    # Salvar como arquivo DICOM
    dicom_filename = os.path.join(output_folder, os.path.basename(jpg_path).replace(".jpg", ".dcm"))
    dicom_file = FileDataset(dicom_filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dicom_file.update(dataset)

    # Configurar atributos para Transfer Syntax compatível
    dicom_file.is_little_endian = True
    dicom_file.is_implicit_VR = True

    dicom_file.save_as(dicom_filename, write_like_original=False)

    return dicom_file

# Enviar DICOM para o PACS
def send_to_pacs(dicom_files, pacs_info):
    ae = AE()

    # Adicionar apenas o contexto de apresentação aceito pelo PACS
    ae.add_requested_context(CTImageStorage, "1.2.840.10008.1.2")  # Implicit VR Little Endian

    assoc = ae.associate(pacs_info["ip"], pacs_info["port"], ae_title=pacs_info["ae_title"])
    if assoc.is_established:
        print("Conexão estabelecida com o PACS.")
        successfully_sent = []
        for dicom_file in dicom_files:
            try:
                print(f"Enviando arquivo: {dicom_file.filename}")
                status = assoc.send_c_store(dicom_file)
                if status and status.Status == 0x0000:
                    print(f"Arquivo enviado com sucesso: {dicom_file.filename}")
                    successfully_sent.append(dicom_file.filename)
                else:
                    print(f"Falha ao enviar: {dicom_file.filename}, Status: {status}")
            except Exception as e:
                print(f"Erro ao enviar arquivo {dicom_file.filename}: {e}")
        assoc.release()
        print("Conexão encerrada com o PACS.")

        # Remover arquivos enviados com sucesso
        for sent_file in successfully_sent:
            try:
                os.remove(sent_file)
                print(f"Arquivo removido: {sent_file}")
            except Exception as e:
                print(f"Erro ao remover arquivo {sent_file}: {e}")
    else:
        print("Falha ao estabelecer conexão com o PACS.")

# Classe principal da aplicação
class PronosConverterApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Pronos Converter")
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setStyleSheet("background-color: #c0c0c0;")

        # Layout
        layout = QtWidgets.QVBoxLayout()

        # Logo
        logo = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap("logo.png")
        logo.setPixmap(pixmap)
        logo.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(logo)

        # Campos de entrada
        self.patient_name_input = QtWidgets.QLineEdit()
        self.patient_name_input.setPlaceholderText("Digite o nome do paciente")
        layout.addWidget(self.patient_name_input)

        self.folder_button = QtWidgets.QPushButton("Selecionar Pasta")
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)

        self.process_button = QtWidgets.QPushButton("Processar")
        self.process_button.clicked.connect(self.process_images)
        layout.addWidget(self.process_button)

        self.setLayout(layout)

    def select_folder(self):
        self.folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if self.folder_path:
            print(f"Pasta selecionada: {self.folder_path}")

    def process_images(self):
        if not hasattr(self, 'folder_path') or not self.folder_path:
            QtWidgets.QMessageBox.warning(self, "Erro", "Por favor, selecione uma pasta primeiro.")
            return

        patient_name = self.patient_name_input.text()
        if not patient_name:
            QtWidgets.QMessageBox.warning(self, "Erro", "Por favor, insira o nome do paciente.")
            return

        config = load_config()
        output_folder = config["output_folder"]
        pacs_info = config["pacs"]

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Gerar UIDs únicos para o estudo e a série do paciente
        study_uid = generate_uid()
        series_uid = generate_uid()

        jpg_files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.lower().endswith(".jpg")]
        dicom_files = []

        for jpg_file in jpg_files:
            dicom_file = convert_to_dicom(jpg_file, patient_name, output_folder, study_uid, series_uid)
            dicom_files.append(dicom_file)

        send_to_pacs(dicom_files, pacs_info)
        QtWidgets.QMessageBox.information(self, "Sucesso", "Todas as imagens foram processadas e enviadas para o PACS.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PronosConverterApp()
    window.show()
    sys.exit(app.exec_())
