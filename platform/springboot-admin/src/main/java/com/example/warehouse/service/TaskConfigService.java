package com.example.warehouse.service;

import com.example.warehouse.model.SparkTaskConfig;
import com.example.warehouse.repository.TaskRepository;
import java.util.Arrays;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class TaskConfigService {
    private final TaskRepository taskRepository;

    public TaskConfigService(TaskRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    public List<SparkTaskConfig> listTasks() {
        List<SparkTaskConfig> tasks = taskRepository.findEnabledTasks();
        if (!tasks.isEmpty()) {
            return tasks;
        }
        SparkTaskConfig offline = new SparkTaskConfig();
        offline.setTaskName("offline_sink");
        offline.setTaskType("SparkStreaming");
        offline.setCommand("python3 streaming/offline_sink/spark_streaming_to_hdfs.py");
        offline.setSchedule("continuous");

        SparkTaskConfig merge = new SparkTaskConfig();
        merge.setTaskName("ods_merge");
        merge.setTaskType("SparkSQL");
        merge.setCommand("./scripts/run_daily_ods_merge.sh ${biz_dt}");
        merge.setSchedule("0 30 2 * * ?");

        return Arrays.asList(offline, merge);
    }

    public void saveTask(SparkTaskConfig task) {
        taskRepository.upsert(task);
    }
}
