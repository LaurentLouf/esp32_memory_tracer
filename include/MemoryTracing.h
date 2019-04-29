#ifndef MEMORYTRACING_H
#define MEMORYTRACING_H

#include <stdint.h>
#include "FreeRTOS.h"
#include "freertos/task.h"

void main_memory_tracing(void* pvParameters);
bool start_memory_tracing(TaskHandle_t& o_task_handle);

#endif  // MEMORYTRACING_H
