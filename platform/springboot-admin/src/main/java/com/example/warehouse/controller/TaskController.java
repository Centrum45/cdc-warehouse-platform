package com.example.warehouse.controller;

import com.example.warehouse.model.SparkTaskConfig;
import com.example.warehouse.service.TaskConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
@Tag(name = "Tasks", description = "Spark task configuration")
public class TaskController {
    private final TaskConfigService taskConfigService;

    public TaskController(TaskConfigService taskConfigService) {
        this.taskConfigService = taskConfigService;
    }

    @GetMapping("/tasks")
    @Operation(summary = "List task configurations")
    public String tasks(Model model) {
        model.addAttribute("tasks", taskConfigService.listTasks());
        SparkTaskConfig task = new SparkTaskConfig();
        task.setTaskName("ods_merge");
        task.setTaskType("SparkSQL");
        task.setCommand("spark-sql -f warehouse/sql/ods/merge/merge_ods_basiccomment_avatar_commentbatchsource_dic.sql");
        task.setSchedule("0 30 2 * * ?");
        model.addAttribute("task", task);
        return "tasks";
    }

    @PostMapping("/tasks")
    @Operation(summary = "Save Spark task configuration")
    public String saveTask(@ModelAttribute SparkTaskConfig task, Model model) {
        taskConfigService.saveTask(task);
        model.addAttribute("tasks", taskConfigService.listTasks());
        model.addAttribute("task", task);
        model.addAttribute("message", "task saved");
        return "tasks";
    }
}
