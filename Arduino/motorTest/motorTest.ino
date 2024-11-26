
int pinoDIR = 8;
int pinoSTEP = 9;
int pinoMS1 = 10;
int pinoMS2 = 11;
int pinoMS3 = 12;
int velocidade = 27; // Define velocidade globally
int tempo;
int count;

void setup() {
  Serial.begin(9600);
  delay(1500);
  
  pinMode(pinoDIR, OUTPUT);
  pinMode(pinoSTEP, OUTPUT);
  pinMode(pinoMS1, OUTPUT);
  pinMode(pinoMS2, OUTPUT);
  pinMode(pinoMS3, OUTPUT);

  count = 0;
  
  digitalWrite(pinoDIR, HIGH);
  digitalWrite(pinoMS1, LOW);
  digitalWrite(pinoMS2, HIGH);
  digitalWrite(pinoMS3, LOW);
}

void loop() {
  count = count + 1;
  tempo = 500000 / velocidade;

  // Move motor for 200 steps in one direction
  for (int i = 0; i < 700; i++) {
    digitalWrite(pinoDIR, HIGH);
    digitalWrite(pinoSTEP, HIGH);
    delayMicroseconds(tempo);
    digitalWrite(pinoSTEP, LOW);
    delayMicroseconds(tempo);
  }

  delay(0); // Adjust the pause time as needed

   for (int i = 0; i < 0; i++) {
    digitalWrite(pinoDIR, LOW);
    digitalWrite(pinoSTEP, HIGH);
    delayMicroseconds(tempo);
    digitalWrite(pinoSTEP, LOW);
    delayMicroseconds(tempo);
  }

  if(count > 3){
    unclog();
  }
}

void unclog() {
  int pog = 500000 / 30;
  count = 0;
  for (int j = 0; j < 6; j++) {
       for (int i = 0; i < 50; i++) {
    digitalWrite(pinoDIR, HIGH);
    digitalWrite(pinoSTEP, HIGH);
    delayMicroseconds(pog);
    digitalWrite(pinoSTEP, LOW);
    delayMicroseconds(pog);
  }
     for (int i = 0; i < 300; i++) {
    digitalWrite(pinoDIR, LOW);
    digitalWrite(pinoSTEP, HIGH);
    delayMicroseconds(pog);
    digitalWrite(pinoSTEP, LOW);
    delayMicroseconds(pog);
  }
  }

}