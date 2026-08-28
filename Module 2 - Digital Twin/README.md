# Module 2 – Digital Twin

## Overview

Module 2 is responsible for creating the digital twin representation of the physical energy management system.

It simulates the behavior of different plant subsystems and maintains their current operational state. The module provides a synchronized digital representation of the physical system for forecasting and further optimization.

---

## Objectives

- Create digital twin models for major plant subsystems.
- Maintain real-time operational states of the system.
- Simulate subsystem behavior.
- Synchronize states across different digital twins.
- Provide a unified system state for the forecasting module.
- Support integration between different plant components.

---

## Folder Structure

    Module 2 - Digital Twin/
    │
    ├── common/
    ├── production/
    ├── boiler/
    ├── compressor/
    ├── hvac/
    ├── solar/
    ├── battery/
    ├── grid/
    ├── integration/
    └── README.md

---

## Digital Twin Components

### Production

Represents the production line and tracks production-related operational parameters.

### Boiler

Models boiler operation and monitors parameters such as fuel consumption and operating conditions.

### Compressor

Represents the air compressor and tracks compressor power and operating state.

### HVAC

Models HVAC operation and monitors temperature and power consumption.

### Solar

Represents the solar energy generation system and its operational state.

### Battery

Models battery energy storage and tracks battery power and state of charge.

### Grid

Represents interaction with the electrical grid, including grid power import.

---

## Core Components

| Component | Responsibility |
|---|---|
| Digital Twin Models | Represent individual physical subsystems |
| State Manager | Maintains the current state of each digital twin |
| Simulation | Simulates subsystem behavior |
| Sync Engine | Synchronizes digital twin states |
| Integration Layer | Connects multiple digital twins into one system |

---

## Workflow

    Physical System
           ↓
    Digital Twin Models
           ↓
    State Management
           ↓
    Simulation
           ↓
    Synchronization
           ↓
    Unified System State
           ↓
    Module 3 - Forecasting

---

## Integration

Module 2 provides the current operational state required by Module 3.

The digital twins are synchronized through the integration layer so that the complete plant can be represented as a unified digital system.

---

## Testing

The integration of the digital twin components can be tested using:

    py -m integration.integration_test

The test verifies:

- Digital twin initialization
- State updates
- Module synchronization
- Component integration
- Unified system state

---

## Technologies Used

- Python 3.11
- Object-Oriented Programming
- JSON
- Digital Twin Modeling
- State Management
- System Synchronization

---

## Module Status

**Status: ✅ Completed**

Module 2 provides the digital representation and synchronized operational state of the plant. It acts as the foundation for the forecasting and optimization modules of the Digital Twin system.