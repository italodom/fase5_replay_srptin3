#include "DHTesp.h" // Inclui a biblioteca para o sensor DHT

// Define o pino onde o sensor DHT22 está conectado
const int DHT_PIN = 15;
// Define o pino onde o LED estará conectado
const int LED_PIN = 2; // Usamos o GPIO 2 para o LED

DHTesp dht; // Cria um objeto DHTesp

void setup() {
  Serial.begin(115200); // Inicia a comunicação serial
  // Aguarda a porta serial abrir (útil para ESP32)
  while (!Serial);

  dht.setup(DHT_PIN, DHTesp::DHT22); // Configura o sensor DHT22

  // Configura o pino do LED como OUTPUT (saída)
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  // Ligar o LED por um breve momento
  digitalWrite(LED_PIN, HIGH); // Acende o LED
  delay(100); // Mantém aceso por 100 milissegundos (0.1 segundo)

  // Desligar o LED
  digitalWrite(LED_PIN, LOW); // Apaga o LED

  // Leitura do sensor DHT
  TempAndHumidity data = dht.getTempAndHumidity();

  // Verifica se a leitura foi bem-sucedida
  if (isnan(data.temperature) || isnan(data.humidity)) {
    Serial.println("Falha ao ler do sensor DHT!");
  } else {
    Serial.print(data.temperature);
    Serial.print(",");
    Serial.print(data.humidity);
    Serial.println("");
  }

  delay(30000); // Espera 30 segundos antes da próxima leitura
}