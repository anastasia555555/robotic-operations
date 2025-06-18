#ifndef MPU6050_KALMAN_POS_H
#define MPU6050_KALMAN_POS_H

#include "stm32g4xx_hal.h"

typedef struct {
    float Q_angle, Q_bias, R_measure;
    float angle, bias, rate;
    float P[2][2];
} KalmanFilter;

typedef struct {
    int16_t Accel_X, Accel_Y, Accel_Z;
    int16_t Gyro_X, Gyro_Y, Gyro_Z;

    float Pitch, Roll, Yaw;
    float dt;

    float Velocity_X, Velocity_Y, Velocity_Z;
    float Position_X, Position_Y, Position_Z;
} MPU6050_Data;

void Kalman_Init(KalmanFilter *k);
float Kalman_GetAngle(KalmanFilter *k, float newAngle, float newRate, float dt);
void MPU6050_Init(I2C_HandleTypeDef *hi2c);

HAL_StatusTypeDef MPU6050_ReadAndEstimatePosition(
    I2C_HandleTypeDef *hi2c, MPU6050_Data *data,
    KalmanFilter *kX, KalmanFilter *kY);

#endif
