/**
 * \brief Small utility for memory tracing
 *
 * \file MemoryTracing.cpp
 * \author Laurent Louf
 */
#include "MemoryTracing.h"
#include "esp_heap_trace.h"
#include "esp_log.h"

#ifdef CONFIG_MEMORY_TRACING_ENABLE_HEAP_TRACES_DUMP
static heap_trace_record_t
    trace_record[CONFIG_MEMORY_TRACING_NUMBER_RECORDS];  // This buffer must be in internal RAM
#endif

static const char* TAG = "MemoryTracing";

static uint32_t get_ccount(void) {
    uint32_t ccount = xthal_get_ccount() & ~3;
#ifndef CONFIG_FREERTOS_UNICORE
    ccount |= xPortGetCoreID();
#endif
    return ccount;
}

void main_memory_tracing(void* pvParameters) {
#ifdef CONFIG_MEMORY_TRACING_ENABLE
#ifdef CONFIG_MEMORY_TRACING_ENABLE_HEAP_TRACES_DUMP
    // Initialize and launch memory tracing
    ESP_ERROR_CHECK(heap_trace_init_standalone(trace_record, CONFIG_MEMORY_TRACING_NUMBER_RECORDS));
    ESP_ERROR_CHECK(heap_trace_start(HEAP_TRACE_LEAKS));
#endif

    uint16_t i_free_heap_display;
    uint32_t ccount;
    while (1) {
#ifdef CONFIG_MEMORY_TRACING_ENABLE_HEAP_TRACES_DUMP
        for (i_free_heap_display = 0;
             i_free_heap_display < CONFIG_MEMORY_TRACING_NB_FREE_HEAP_DISPLAY_BEFORE_TRACE_DUMP;
             i_free_heap_display++) {
            vTaskDelay(CONFIG_MEMORY_TRACING_INTERVAL_DISPLAY_FREE_HEAP_MS / portTICK_PERIOD_MS);
            ccount = get_ccount();
            ESP_LOGI(TAG, "Free heap size %d, ccount 0x%08x, core %d", esp_get_free_heap_size(),
                     ccount & ~3, ccount & 1);
        }

        heap_trace_dump();
#else
        vTaskDelay(CONFIG_MEMORY_TRACING_INTERVAL_DISPLAY_FREE_HEAP_MS / portTICK_PERIOD_MS);
        ccount = get_ccount();
        ESP_LOGI(TAG, "Free heap size %d, ccount 0x%08x, core %d", esp_get_free_heap_size(),
                 ccount & ~3, ccount & 1);
#endif
    }
#endif
}

bool start_memory_tracing(TaskHandle_t& o_task_handle) {
#ifdef CONFIG_MEMORY_TRACING_ENABLE
    TaskHandle_t task_handle = NULL;
    if (xTaskCreate(main_memory_tracing, "MEMORY_TRACING", CONFIG_MEMORY_TRACING_TASK_STACK_SIZE,
                    NULL, tskIDLE_PRIORITY + 2, &task_handle) == pdPASS) {
        o_task_handle = task_handle;
        return true;
    } else {
        o_task_handle = NULL;
        return false;
    }
#else
    o_task_handle = NULL;
    return false;
#endif
}