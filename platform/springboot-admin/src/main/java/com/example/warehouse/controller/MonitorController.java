package com.example.warehouse.controller;

import com.example.warehouse.service.MonitorService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class MonitorController {
    private final MonitorService monitorService;

    public MonitorController(MonitorService monitorService) {
        this.monitorService = monitorService;
    }

    @GetMapping("/monitors")
    public String monitors(Model model) {
        model.addAttribute("items", monitorService.listMonitorItems());
        model.addAttribute("results", monitorService.listLatestResults());
        return "monitors";
    }
}
