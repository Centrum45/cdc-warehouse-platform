package com.example.warehouse.controller;

import com.example.warehouse.service.MonitorService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@Tag(name = "Monitors", description = "Data quality and pipeline monitors")
public class MonitorController {
    private final MonitorService monitorService;

    public MonitorController(MonitorService monitorService) {
        this.monitorService = monitorService;
    }

    @GetMapping("/monitors")
    @Operation(summary = "List monitor items and latest results")
    public String monitors(Model model) {
        model.addAttribute("items", monitorService.listMonitorItems());
        model.addAttribute("results", monitorService.listLatestResults());
        return "monitors";
    }
}
