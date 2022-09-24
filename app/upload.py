from werkzeug.utils import secure_filename
import os

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = basedir + "/../uploads"
ALLOWED_EXTENSIONS = {"tex", "docx"}


def get_name(filename):
    return filename.rsplit('.', 1)[0].upper()

def get_full_path(filename):
    return UPLOAD_FOLDER + "/" + filename

def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename):
    return '.' in filename and get_extension(filename) in ALLOWED_EXTENSIONS


def upload_file(request):
    if 'document' not in request.files:
        return None, "No file found"

    file = request.files['document']

    if file.filename == '':
        return None, "Filename blank"

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename, get_extension(filename)

    return None, "Extension not allowed"


def delete_file(request):
    file = request.files['document']
    filename = secure_filename(file.filename)

    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
