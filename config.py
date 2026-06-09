import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    db_host:     str = os.getenv("DB_HOST", "localhost")
    db_port:     int = int(os.getenv("DB_PORT", 5432))
    db_name:     str = os.getenv("DB_NAME", "energy_compliance")
    db_user:     str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    output_dir:  str = os.getenv("OUTPUT_DIR", "outputs")
    log_level:   str = os.getenv("LOG_LEVEL", "INFO")
    aws_bucket:  str = os.getenv("AWS_S3_BUCKET", "")
    aws_region:  str = os.getenv("AWS_REGION", "eu-west-2")

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


config = Config()
