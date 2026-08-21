import uvicorn

from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    config = Config()
    uvicorn.run(
        "run:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
