from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session
from pydantic import BaseModel
from langchain.agents.structured_output import ProviderStrategy, ToolStrategy
from dotenv import load_dotenv
import os

load_dotenv()

# DB bağlantısını .env den oku değişkene ata
SQLALCHEMY_DATABASE_URL=os.getenv('SQLALCHEMY_DATABASE_URL')

# DB bağlantı engine oluştur
engine = create_engine(url=SQLALCHEMY_DATABASE_URL)

# Hem yapay zekanın yapısal çıktı üreteceği hem de veri tabanı tablosunun yaratılacağı sınıfı tanımla
class CityWeather(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    temperature: float = Field(..., description="Current temperature of the city")
    measure_type: str = Field(..., description="Unit of measurement, e.g., 'Celsius' or 'Fahrenheit'")
    date_time: datetime = Field(..., description="Timestamp of the weather reading")
    
    # Using Optional for prediction fields in case it's a current-only report
    prediction_day: Optional[str] = Field(None, description="Day or date for the forecast")
    prediction_temp: Optional[float] = Field(None, description="Forecasted temperature")
    weather_status: Optional[str] = Field(None, description="Weather condition, e.g., 'Sunny', 'Rainy'")

# SQLModel sınıftan türetilen (inherit) 
SQLModel.metadata.create_all(engine)

# Initialize the model
model = init_chat_model(
    model="gemini-2.5-flash-lite", 
    model_provider="google_genai", 
    max_tokens=300
)

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"You have searched this: {query}"

agent = create_agent(
    model=model,
    tools=[search],
    response_format=ToolStrategy(CityWeather)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract structured output from: Ankara'da hava sıcaklığı 22 C parçalı bulutlu 5 gün sonra yağmurlu olacak."}]
})

print(result['structured_response'])

# Veri tabanına yazılacak obje. id burada kasıtlı boş DB tarafında otomatik dolduruluyor.
weather_entry = CityWeather(
    temperature=result['structured_response'].temperature,
    measure_type=result['structured_response'].measure_type,
    date_time=datetime.now(), # Generates the current timestamp
    prediction_day=result['structured_response'].prediction_day,
    prediction_temp=result['structured_response'].prediction_temp,
    weather_status=result['structured_response'].weather_status
)

# Veri tabanına bir session aç kaydı (weather_entry) gir ve session kapat.
with Session(engine) as session:
    session.add(weather_entry)
    session.commit()
   



# binded_model = model.with_structured_output(CityWeather)

# result = binded_model.invoke(input="Extract structured output from: Ankara'da hava sıcaklığı 22 C parçalı bulutlu 5 gün sonra yağmurlu olacak.")

# print(result)