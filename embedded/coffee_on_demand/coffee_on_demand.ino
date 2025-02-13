#include <SPI.h>
#include <Adafruit_GFX.h>  // hardware-specific library
#include <MCUFRIEND_kbv.h> // hardware-specific library
#include "qrcode.h"
#include <TouchScreen.h>
#include <Fonts/FreeSans9pt7b.h>

MCUFRIEND_kbv tft;

uint16_t rgb888ToRgb565(uint32_t color)
{
  uint8_t r = (color >> 16) & 0xFF;
  uint8_t g = (color >> 8) & 0xFF;
  uint8_t b = color & 0xFF;
  return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}

#define WHITE 0xFFFF
#define COFFEE_ON_DEMAND_1 rgb888ToRgb565(0x717C89)
#define COFFEE_ON_DEMAND_2 rgb888ToRgb565(0x420217)

const unsigned char coffee_bean[] PROGMEM = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xc0, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f,
                                             0xff, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xc0, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff,
                                             0xfe, 0x03, 0xff, 0xf0, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfe, 0x07, 0xff, 0xf0, 0x00, 0x00,
                                             0x00, 0x1f, 0xff, 0xff, 0xf8, 0x07, 0xfe, 0x00, 0x00, 0x00, 0x03, 0x8f, 0xff, 0xff, 0xf8, 0xff,
                                             0xfe, 0x06, 0x00, 0x00, 0x03, 0x8f, 0xff, 0xff, 0xf8, 0xff, 0xfe, 0x06, 0x00, 0x00, 0x03, 0xe0,
                                             0x1f, 0xff, 0xc1, 0xff, 0xf8, 0xff, 0x80, 0x00, 0x03, 0xe0, 0x1f, 0xff, 0xc7, 0xff, 0xf0, 0xff,
                                             0x80, 0x00, 0x03, 0xf0, 0x00, 0x07, 0x07, 0xff, 0xf0, 0xff, 0x80, 0x00, 0x03, 0xff, 0xe0, 0x03,
                                             0x1f, 0xff, 0xf0, 0xff, 0x80, 0x00, 0x03, 0xff, 0xe0, 0x03, 0x1f, 0xff, 0xf0, 0xff, 0x80, 0x00,
                                             0x03, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xc7, 0xff, 0x80, 0x00, 0x03, 0xff, 0xff, 0xf8, 0xff, 0xff,
                                             0xc7, 0xff, 0x80, 0x00, 0x03, 0xff, 0xff, 0xf8, 0xff, 0xff, 0xc7, 0xff, 0x80, 0x00, 0x00, 0x7f,
                                             0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff,
                                             0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8,
                                             0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00,
                                             0x00, 0x1f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x0f, 0xff, 0xf8, 0xff, 0xfe,
                                             0x3f, 0xff, 0x80, 0x00, 0x00, 0x0f, 0xff, 0xf8, 0xff, 0xf8, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x03,
                                             0xff, 0xf8, 0xff, 0xf8, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x03, 0xff, 0xf8, 0xff, 0xf8, 0xff, 0xfe,
                                             0x00, 0x00, 0x00, 0x00, 0x1f, 0xf8, 0xff, 0xf8, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x1f, 0xf8,
                                             0xff, 0xf8, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xf8, 0xff, 0xe1, 0xff, 0xfc, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x18, 0xff, 0xc7, 0xff, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0xff, 0xc7,
                                             0xff, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xc7, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0xff, 0xc7, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xc7, 0xff, 0x80,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x1f, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x18, 0x3f, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xe0, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x07, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0xff,
                                             0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// QR code options

#define qrPixel 4
#define position_x 22
#define position_y 135
#define border 2

// state machine states
enum states
{
  none,
  idle,
  listening,
  dispensing,
  talking,
  processing,
  payment,
  registering
};

String received_message;

states priorstate, state;

int weight;
int weightChanged = 0;
String pix;
String  price;

void setup()
{
  Serial.begin(9600);
  while (!Serial)
  {
    ; // wait for serial port to connect. Needed for native USB
  }
  initializeDisplay();
  priorstate = none;
  state = idle;
  tft.setFont(&FreeSans9pt7b);
}

void loop(void)
{
  updateInfo();
  switch (state)
  {
  case idle:
    idle_state();
    break;
  case listening:
    listening_state();
    break;
  case registering:
    registering_state();
    break;
  case dispensing:
    dispensing_state();
    break;
  case processing:
    processing_state();
    break;
  case talking:
    talking_state();
  case payment:
    payment_state();
  }
}

void updateInfo()
{

  if (Serial.available() > 0)
  {
    received_message = "";
    received_message = Serial.readStringUntil('\n');
    
    if (received_message == "UPDATE:STATE:IDLE")
    {
      state = idle;
    }
    else if (received_message == "UPDATE:STATE:LISTENING")
    {
      state = listening;
    }
    else if (received_message == "UPDATE:STATE:TALKING")
    {
      state = talking;
    }
    else if (received_message == "UPDATE:STATE:DISPENSING")
    {
      state = dispensing;
    }
    else if (received_message == "UPDATE:STATE:PROCESSING")
    {
      state = processing;
    }
    else if (received_message == "UPDATE:STATE:REGISTERING")
    {
      state = registering;
    }

    int index = received_message.indexOf("UPDATE:WEIGHT:");
    

    if (index != -1)
    {
      String weightStr = received_message.substring(index + 14);
      weight = atoi(weightStr.c_str());
      weightChanged = 1;
    }

    index = received_message.indexOf("UPDATE:PRICE:");
    if (index != -1)
    {
        String priceString = received_message.substring(index + 13);
        Serial.print("Updated string price: ");
        Serial.println(priceString);

        // Convertendo para um número inteiro
        int priceInt = priceString.toInt();

        // Convertendo para string no formato 00.00
        char formattedPrice[10];
        sprintf(formattedPrice, "R$ %02d.%02d", priceInt / 100, priceInt % 100);
        price = formattedPrice;
        Serial.print("Updated price: ");
        Serial.println(formattedPrice);
    }

    index = received_message.indexOf("UPDATE:PIX:");
    if (index != -1)
    {
      state = payment;
      pix = received_message.substring(index + 11);
      Serial.print("Updated pix: ");
      Serial.println(pix);
    }
  }
}

void idle_state()
{
  if (state != priorstate)
  {
    priorstate = state;

    tft.fillScreen(WHITE);
    drawBigLogo();

    tft.setTextColor(COFFEE_ON_DEMAND_1);
    tft.setTextSize(1);
    tft.setCursor(40, 150);
    tft.print("Coffee on Demand");
  }
}

void registering_state()
{
  if (state != priorstate)
  {
    priorstate = state;
    tft.fillScreen(WHITE);
    tft.setTextColor(COFFEE_ON_DEMAND_1);
    tft.setTextSize(2);
    tft.setCursor(25, 150);
    tft.print("Taking your");
    tft.setCursor(45, 190);
    tft.print("pictures :)");
  }
}

void talking_state()
{
  if (state != priorstate)
  {
    priorstate = state;
    tft.fillScreen(WHITE);
    tft.setTextColor(COFFEE_ON_DEMAND_1);
    tft.setTextSize(2);
    tft.setCursor(40, 150);
    tft.print("Talking...");
  }
}

void processing_state()
{
  if (state != priorstate)
  {
    priorstate = state;
    tft.fillScreen(WHITE);
    tft.setTextColor(COFFEE_ON_DEMAND_1);
    tft.setTextSize(2);
    tft.setCursor(20, 150);
    tft.print("Processing...");
  }
}

void listening_state()
{
  if (state != priorstate)
  {
    priorstate = state;
    tft.fillScreen(WHITE);
    tft.setTextColor(COFFEE_ON_DEMAND_1);
    tft.setTextSize(2);
    tft.setCursor(40, 150);
    tft.print("Listening...");
  }
}

void dispensing_state()
{
  if (state != priorstate)
  {
    priorstate = state;
    weightChanged = 0;
    tft.fillScreen(WHITE);
    tft.setTextColor(COFFEE_ON_DEMAND_1);
    
    // Display header
    tft.setCursor(24, 150);
    tft.setTextSize(2);
    tft.println("Dispensing...");
    

    // Display the weight of the coffee
    char dynamicString[20];
    sprintf(dynamicString, "%dg", weight);
    tft.setCursor(90, 230);
    tft.setTextSize(3);
    tft.println(dynamicString);
    
  }

  if (weightChanged)
  {
    weightChanged = 0;
    // Clear the area that shows both weight and price.
    tft.fillRect(40, 170, 150, 140, WHITE);
    
    // Update weight display
    char dynamicString[20];
    sprintf(dynamicString, "%dg", weight);
    if (strlen(dynamicString) == 2) {
      tft.setCursor(90, 230);
    } else if (strlen(dynamicString) == 3) {
      tft.setCursor(75, 230);
    } else if (strlen(dynamicString) == 4) {
      tft.setCursor(55, 230);
    }
    tft.setTextSize(3);
    tft.println(dynamicString);
    
  }
}


void payment_state()
{

  if (state != priorstate)
  {
    // Display the value of the coffee (price)
    priorstate = state;
    tft.fillScreen(WHITE);
    drawFinalizado();
    displayQRcode(pix.c_str());
  }

}

void drawBigLogo()
{
  tft.drawBitmap(78, 155, coffee_bean, 75, 59, COFFEE_ON_DEMAND_2); // 75x59px
}

void drawFinalizado()
{
  tft.setTextColor(COFFEE_ON_DEMAND_1);
  tft.setCursor(25, 47);
  tft.setTextSize(2);
  tft.print("All set!");
  tft.write(0x02);
  tft.println();
  tft.setCursor(25, 77);
  tft.println(price);
  tft.setCursor(25, 96);
  tft.setTextSize(1);
  tft.println("Read the QR-code below ");
  tft.setCursor(25, 115);
  tft.println("with your banking app");
}

void initializeDisplay()
{
  uint16_t ID;
  ID = tft.readID(); // valid for Uno shields

  tft.reset();
  tft.begin(ID);      // initialize SPI bus
  tft.setRotation(0); // landscape
  tft.fillScreen(WHITE);
}

#define version 8
uint8_t qrcodeData[301];

void displayQRcode(const char *text)
{
  QRCode qrcode;
  int size = 4 * version + 17;

  qrcode_initText(&qrcode, qrcodeData, version, 0, text);

  tft.fillRoundRect(position_x - border, position_y - border, size * qrPixel + border * 2, size * qrPixel + border * 2, 4, COFFEE_ON_DEMAND_2);
  tft.fillRoundRect(position_x - border + 3, position_y - border + 3, size * qrPixel + (border - 3) * 2, size * qrPixel + (border - 3) * 2, 4, WHITE);

  for (uint8_t y = 0; y < size; y++)
  {
    for (uint8_t x = 0; x < size; x++)
    {
      if (qrcode_getModule(&qrcode, x, y))
      {
        tft.fillRect(position_x + x * qrPixel, position_y + y * qrPixel, qrPixel, qrPixel, COFFEE_ON_DEMAND_2);
      }
    }
  }
}
