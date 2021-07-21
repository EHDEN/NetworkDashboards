
class FileUploadingException(Exception):
    pass


class FilesExtractorException(FileUploadingException):
    pass


class UnsupportedExtension(FilesExtractorException):
    pass


class InvalidZipFile(FilesExtractorException):
    pass


class InvalidZipFileFormat(InvalidZipFile):
    pass


class BothNomenclaturesUsed(InvalidZipFile):
    pass


class NoExpectedFiles(InvalidZipFile):
    pass


class FileChecksException(FileUploadingException):
    pass


class InvalidFileFormat(FileChecksException):
    pass


class InvalidFieldValue(FileChecksException):
    pass


class DuplicatedMetadataRow(FileChecksException):
    pass


class MissingFieldValue(FileChecksException):
    pass


class InvalidFileExtension(FileChecksException):
    pass
