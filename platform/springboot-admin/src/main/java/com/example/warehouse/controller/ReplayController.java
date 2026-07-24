package com.example.warehouse.controller;

import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.ReplayRequest;
import com.example.warehouse.service.ReplayService;
import java.time.LocalDate;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
@Tag(name = "Replay", description = "Maxwell bootstrap / replay operations")
public class ReplayController {
    private final ReplayService replayService;

    public ReplayController(ReplayService replayService) {
        this.replayService = replayService;
    }

    @GetMapping("/replay")
    @Operation(summary = "Replay form page")
    public String replay(Model model) {
        ReplayRequest request = new ReplayRequest();
        request.setDatabaseName("basiccomment");
        request.setTableName("avatar_commentbatchsource");
        request.setStartTime(LocalDate.now().minusDays(1) + " 00:00:00");
        request.setEndTime(LocalDate.now() + " 00:00:00");
        model.addAttribute("request", request);
        model.addAttribute("records", replayService.latest());
        return "replay";
    }

    @PostMapping("/replay")
    @Operation(summary = "Execute a full MySQL snapshot replay")
    public String submit(@ModelAttribute ReplayRequest request, Model model) {
        model.addAttribute("request", request);
        try {
            CommandResult result = replayService.execute(request);
            model.addAttribute("command", replayService.buildBootstrapCommand(request));
            model.addAttribute("result", result);
        } catch (IllegalArgumentException ex) {
            model.addAttribute("error", ex.getMessage());
        }
        model.addAttribute("records", replayService.latest());
        return "replay";
    }
}
