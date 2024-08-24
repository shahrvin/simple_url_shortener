from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import validators
from . import schemas, models, crud
from .database import SessionLocal, engine
from starlette.datastructures import URL
from .config import get_settings 

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    print(base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    print(admin_endpoint)
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url

@app.get("/")
def read_root():
    return "this is a url shortener :))"


def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)
def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist!!"
    raise HTTPException(status_code=404, detail=message)


@app.post("/url",  response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    # chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    # key = "".join(secrets.choice(chars) for _ in range(5))
    # secret_key= "".join(secrets.choice(chars) for _ in range(8))
    # db_url = models.URL(
    #     target_url=url.target_url, key=key, secret_key=secret_key
    # )
    # db.add(db_url)
    # db.commit()
    # db.refresh(db_url)
    # db_url.url = key
    # db_url.admin_url = secret_key
    db_url= crud.create_db_url(db= db, url=url)
    

    return get_admin_info(db_url)

@app.get("/{url_key}")
def forward_to_target_url(url_key: str, request: Request, db: Session = Depends(get_db)):
    # db_url = (db.query(models.URL).filter(models.URL.key == url_key, models.URL.is_active).first())
    
    if db_url := crud.get_db_url_by_key(db= db, url_key=url_key):
        crud.update_db_clicks(db=db,db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else: 
        return raise_not_found(request)
    

@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model= schemas.URLInfo
)
def get_url_info(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url:= crud.get_db_url_by_secret(db, secret_key=secret_key):
        
        return get_admin_info(db_url)
    return raise_not_found(request)



@app.get("/all_urls/")
def get_urls(db: Session = Depends(get_db)):
    urls = crud.get_all_db_urls(db)
    
    return urls

@app.delete("/admin/{secret_key}")
def delete_url(secret_key:str, request: Request, db:Session = Depends(get_db)):
    if db_url := crud.deactivate_db_url_by_secret(db=db, secret_key=secret_key):
        message = f"Succesfuly deleted shortened url for '{db_url.target_url}'"
        return {"detail": message}
    else: 
        raise_not_found(request)
     
