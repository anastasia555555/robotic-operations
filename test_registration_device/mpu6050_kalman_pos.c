#include "mpu6050_kalman_pos.h"
#include <math.h>

#define MPU6050_ADDR         (0x68 << 1)
#define MPU6050_REG_PWR_MGMT 0x6B
#define MPU6050_REG_ACCEL_X  0x3B
#define RAD_TO_DEG 57.2957795131f
#define G 9.81f

static uint32_t lastUpdate = 0;

void Kalman_Init(KalmanFilter *k) {
    k->Q_angle = 0.001f;
    k->Q_bias = 0.003f;
    k->R_measure = 0.03f;
    k->angle = 0.0f;
    k->bias = 0.0f;
    k->P[0][0] = k->P[0][1] = k->P[1][0] = k->P[1][1] = 0.0f;
}

float Kalman_GetAngle(KalmanFilter *k, float newAngle, float newRate, float dt) {
    k->rate = newRate - k->bias;
    k->angle += dt * k->rate;

    k->P[0][0] += dt * (dt*k->P[1][1] - k->P[0][1] - k->P[1][0] + k->Q_angle);
    k->P[0][1] -= dt * k->P[1][1];
    k->P[1][0] -= dt * k->P[1][1];
    k->P[1][1] += k->Q_bias * dt;

    float S = k->P[0][0] + k->R_measure;
    float K[2] = { k->P[0][0] / S, k->P[1][0] / S };
    float y = newAngle - k->angle;

    k->angle += K[0] * y;
    k->bias += K[1] * y;

    float P00 = k->P[0][0], P01 = k->P[0][1];
    k->P[0][0] -= K[0] * P00;
    k->P[0][1] -= K[0] * P01;
    k->P[1][0] -= K[1] * P00;
    k->P[1][1] -= K[1] * P01;

    return k->angle;
}

void MPU6050_Init(I2C_HandleTypeDef *hi2c) {
    uint8_t data = 0x00;
    HAL_I2C_Mem_Write(hi2c, MPU6050_ADDR, MPU6050_REG_PWR_MGMT, 1, &data, 1, HAL_MAX_DELAY);
    lastUpdate = HAL_GetTick();
}

HAL_StatusTypeDef MPU6050_ReadAndEstimatePosition(
    I2C_HandleTypeDef *hi2c, MPU6050_Data *data,
    KalmanFilter *kX, KalmanFilter *kY) {

    uint8_t buf[14];
    if (HAL_I2C_Mem_Read(hi2c, MPU6050_ADDR, MPU6050_REG_ACCEL_X, 1, buf, 14, HAL_MAX_DELAY) != HAL_OK)
        return HAL_ERROR;

    data->Accel_X = (int16_t)(buf[0] << 8 | buf[1]);
    data->Accel_Y = (int16_t)(buf[2] << 8 | buf[3]);
    data->Accel_Z = (int16_t)(buf[4] << 8 | buf[5]);
    data->Gyro_X = (int16_t)(buf[8] << 8 | buf[9]);
    data->Gyro_Y = (int16_t)(buf[10] << 8 | buf[11]);
    data->Gyro_Z = (int16_t)(buf[12] << 8 | buf[13]);

    float ax = data->Accel_X / 16384.0f;
    float ay = data->Accel_Y / 16384.0f;
    float az = data->Accel_Z / 16384.0f;

    float gx = data->Gyro_X / 131.0f;
    float gy = data->Gyro_Y / 131.0f;
    float gz = data->Gyro_Z / 131.0f;

    uint32_t now = HAL_GetTick();
    data->dt = (now - lastUpdate) / 1000.0f;
    lastUpdate = now;

    float pitch = atan2f(ay, sqrtf(ax * ax + az * az)) * RAD_TO_DEG;
    float roll  = atan2f(-ax, sqrtf(ay * ay + az * az)) * RAD_TO_DEG;

    data->Pitch = Kalman_GetAngle(kX, pitch, gx, data->dt);
    data->Roll  = Kalman_GetAngle(kY, roll, gy, data->dt);
    data->Yaw  += gz * data->dt;

    float ax_corr = ax - sinf(data->Pitch / RAD_TO_DEG);
    float ay_corr = ay - sinf(data->Roll / RAD_TO_DEG);
    float az_corr = az - cosf(data->Pitch / RAD_TO_DEG) * cosf(data->Roll / RAD_TO_DEG);

    data->Velocity_X += ax_corr * G * data->dt;
    data->Velocity_Y += ay_corr * G * data->dt;
    data->Velocity_Z += az_corr * G * data->dt;

    data->Position_X += data->Velocity_X * data->dt;
    data->Position_Y += data->Velocity_Y * data->dt;
    data->Position_Z += data->Velocity_Z * data->dt;

    return HAL_OK;
}
