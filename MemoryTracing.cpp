/**
 * \brief Small utility for memory tracing
 *
 * \file MemoryTracing.cpp
 * \author Laurent Louf
 */
#include "MemoryTracing.h"
#include "esp_heap_trace.h"
#include "esp_log.h"

#define MEMORY_TRACING_INTERVAL_FREE_HEAP_DISPLAY_MS (1000 * 5)
#define MEMORY_TRACING_NB_FREE_HEAP_DISPLAY_BEFORE_TRACE_DUMP 6
#define MEMORY_TRACING_NUMBER_RECORDS 400
static heap_trace_record_t
    trace_record[MEMORY_TRACING_NUMBER_RECORDS];  // This buffer must be in internal RAM

static const char* TAG = "MemoryTracing";

static uint32_t get_ccount(void) {
    uint32_t ccount = xthal_get_ccount() & ~3;
#ifndef CONFIG_FREERTOS_UNICORE
    ccount |= xPortGetCoreID();
#endif
    return ccount;
}

void main_memory_tracing(void* pvParameters) {
    // Initialize and launch memory tracing
    ESP_ERROR_CHECK(heap_trace_init_standalone(trace_record, MEMORY_TRACING_NUMBER_RECORDS));
    ESP_ERROR_CHECK(heap_trace_start(HEAP_TRACE_LEAKS));

    uint8_t i_free_heap_display;
    uint32_t ccount;
    while (1) {
        for (i_free_heap_display = 0;
             i_free_heap_display < MEMORY_TRACING_NB_FREE_HEAP_DISPLAY_BEFORE_TRACE_DUMP;
             i_free_heap_display++) {
            vTaskDelay(MEMORY_TRACING_INTERVAL_FREE_HEAP_DISPLAY_MS / portTICK_PERIOD_MS);
            ccount = get_ccount();
            ESP_LOGI(TAG, "Free heap size %d, ccount 0x%08x, core %d", esp_get_free_heap_size(),
                     ccount & ~3, ccount & 1);
        }
        heap_trace_dump();
    }
}

bool start_memory_tracing(TaskHandle_t& o_task_handle) {
    TaskHandle_t task_handle = NULL;
    if (xTaskCreate(main_memory_tracing, "MEMORY_TRACING", 2048, NULL, tskIDLE_PRIORITY + 2,
                    &task_handle) == pdPASS) {
        o_task_handle = task_handle;
        return true;
    } else {
        return false;
    }
}