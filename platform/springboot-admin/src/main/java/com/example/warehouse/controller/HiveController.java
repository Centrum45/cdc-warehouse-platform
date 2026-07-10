package com.example.warehouse.controller;

import com.example.warehouse.model.HiveQueryRequest;
import com.example.warehouse.model.HiveQueryResult;
import com.example.warehouse.service.HiveQueryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/hive")
@Tag(name = "Hive", description = "Hive query console")
public class HiveController {
    private final HiveQueryService hiveQueryService;

    public HiveController(HiveQueryService hiveQueryService) {
        this.hiveQueryService = hiveQueryService;
    }

    @PostMapping("/query")
    @Operation(summary = "Run a safe Hive query")
    public HiveQueryResult query(@RequestBody HiveQueryRequest request) {
        return hiveQueryService.query(request);
    }
}
