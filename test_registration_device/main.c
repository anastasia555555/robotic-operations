#include "main.h"
#include "mpu6050_kalman_pos.h"
#include <stdio.h>

I2C_HandleTypeDef hi2c1;
UART_HandleTypeDef huart2;

MPU6050_Data mpuData;
KalmanFilter kX, kY;

#define BTN_RESET_PIN GPIO_PIN_0
#define BTN_RESET_PORT GPIOA

void reset_displacement(MPU6050_Data *data) {
    data->Velocity_X = data->Velocity_Y = data->Velocity_Z = 0.0f;
    data->Position_X = data->Position_Y = data->Position_Z = 0.0f;
}

int main(void) {
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_I2C1_Init();
    MX_USART2_UART_Init();

    Kalman_Init(&kX);
    Kalman_Init(&kY);
    MPU6050_Init(&hi2c1);

    char msg[128];
    while (1) {
        if (MPU6050_ReadAndEstimatePosition(&hi2c1, &mpuData, &kX, &kY) == HAL_OK) {
            if (HAL_GPIO_ReadPin(BTN_RESET_PORT, BTN_RESET_PIN) == GPIO_PIN_SET) {
                reset_displacement(&mpuData);
                snprintf(msg, sizeof(msg), "Origin set to (0, 0, 0)\r\n");
                HAL_UART_Transmit(&huart2, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);
                HAL_Delay(300);  // Debounce delay
            }

            snprintf(msg, sizeof(msg),
                     "Pitch: %.1f°, Roll: %.1f°, X: %.3f m, Y: %.3f m, Z: %.3f m\r\n",
                     mpuData.Pitch, mpuData.Roll,
                     mpuData.Position_X, mpuData.Position_Y, mpuData.Position_Z);
            HAL_UART_Transmit(&huart2, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);
        }

        HAL_Delay(50);
    }
}
