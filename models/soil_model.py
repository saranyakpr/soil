"""
╔══════════════════════════════════════════════════════════════════════════╗
║          SOIL VISION 360 — Soil Intelligence Model (soil_model.py)       ║
║                                                                          ║
║   Full-stack soil classification engine covering:                        ║
║   • RGB-based color classification                                       ║
║   • Multi-metric scoring (water, crop, construction, heat)               ║
║   • Advanced analytics (ROI, flood risk, climate impact)                 ║
║   • Crop compatibility matrix                                            ║
║   • Construction risk assessment                                         ║
║   • Land potential composite score                                       ║
║   • Soil ID generation                                                   ║
║   • Nutrient profiling                                                   ║
║   • Seasonal planning                                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import math
import random
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from enum import Enum
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import json


def get_soil_layers(soil_type):

    path = os.path.join(os.path.dirname(__file__), "soil_layers_dataset.json")

    with open(path) as f:
        data = json.load(f)

    return data.get(soil_type, {}).get("layers", [])


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class SoilCategory(str, Enum):
    BLACK = "Black Soil"
    RED = "Red Soil"
    CLAY = "Clay Soil"
    ALLUVIAL = "Alluvial Soil"
    CINDER = "Cinder Soil"
    LATERITE = "Laterite Soil"
    PEAT = "Peat Soil"
    YELLOW = "Yellow Soil"
    UNKNOWN = "Unknown Soil"


class RiskLevel(str, Enum):
    LOW      = "Low"
    MEDIUM   = "Medium"
    HIGH     = "High"
    CRITICAL = "Critical"
    VERY_HIGH = "Very High"


class SoilTexture(str, Enum):
    SANDY         = "Sandy"
    SANDY_LOAM    = "Sandy_Loam"
    LOAMY_SAND    = "Loamy Sand"
    LOAM          = "Loam"
    SILT_LOAM     = "Silt Loam"
    CLAY_LOAM     = "Clay Loam"
    HEAVY_CLAY    = "Heavy Clay"
    SILTY_CLAY    = "Silty Clay"


class Fertility(str, Enum):
    VERY_LOW  = "Very Low"
    LOW       = "Low"
    MODERATE  = "Moderate"
    HIGH      = "High"
    VERY_HIGH = "Very High"


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RGBColor:
    """Represents average RGB of a soil image"""
    r: int = 0
    g: int = 0
    b: int = 0

    @property
    def brightness(self) -> float:
        return (self.r + self.g + self.b) / (3 * 255)

    @property
    def redness_ratio(self) -> float:
        denom = self.g + self.b + 1
        return self.r / denom

    @property
    def yellowness_ratio(self) -> float:
        denom = self.b * 2 + 1
        return (self.r + self.g) / denom

    @property
    def greenness_ratio(self) -> float:
        denom = self.r + self.b + 1
        return self.g / denom

    @property
    def saturation(self) -> float:
        max_c = max(self.r, self.g, self.b)
        min_c = min(self.r, self.g, self.b)
        if max_c == 0:
            return 0.0
        return (max_c - min_c) / max_c

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_dict(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b, "hex": self.to_hex()}


@dataclass
class NutrientProfile:
    """Soil nutrient levels (0–100 scale)"""
    nitrogen: int       = 50
    phosphorus: int     = 50
    potassium: int      = 50
    organic_matter: int = 50
    calcium: int        = 50
    magnesium: int      = 50
    sulfur: int         = 40
    iron: int           = 45
    zinc: int           = 35

    @property
    def overall_fertility(self) -> int:
        weights = {
            "nitrogen": 0.25, "phosphorus": 0.20, "potassium": 0.20,
            "organic_matter": 0.20, "calcium": 0.05, "magnesium": 0.05,
            "sulfur": 0.03, "iron": 0.01, "zinc": 0.01
        }
        score = sum(getattr(self, k) * v for k, v in weights.items())
        return round(score)

    @property
    def fertility_label(self) -> str:
        s = self.overall_fertility
        if s >= 80: return Fertility.VERY_HIGH
        if s >= 65: return Fertility.HIGH
        if s >= 45: return Fertility.MODERATE
        if s >= 25: return Fertility.LOW
        return Fertility.VERY_LOW

    def to_dict(self) -> dict:
        return {
            "nitrogen": self.nitrogen,
            "phosphorus": self.phosphorus,
            "potassium": self.potassium,
            "organic_matter": self.organic_matter,
            "calcium": self.calcium,
            "magnesium": self.magnesium,
            "sulfur": self.sulfur,
            "iron": self.iron,
            "zinc": self.zinc,
            "overall_fertility": self.overall_fertility,
            "fertility_label": self.fertility_label,
        }


@dataclass
class CoreScores:
    """Primary soil analysis scores"""
    water_retention: int    = 0
    crop_score: int         = 0
    construction_score: int = 0
    heat_index: int         = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdvancedAnalytics:
    """Extended analytics beyond core scores"""
    land_potential_score: int    = 0
    agriculture_roi: float       = 0.0
    construction_risk: str       = RiskLevel.MEDIUM
    flood_risk: str              = RiskLevel.LOW
    drought_risk: str            = RiskLevel.MEDIUM
    erosion_risk: str            = RiskLevel.LOW
    carbon_sequestration: str    = "Medium"
    drought_sensitivity: str     = "Medium"
    temperature_rise_effect: str = "Moderate"
    climate_trend: str           = "Stable"
    estimated_cost_factor: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CropRecommendation:
    """Crop suggestions per soil type"""
    primary: List[str]          = field(default_factory=list)
    secondary: List[str]        = field(default_factory=list)
    avoid: List[str]            = field(default_factory=list)
    season: str                 = ""
    irrigation: str             = ""
    fertilizer: str             = ""
    spacing_cm: str             = ""
    expected_yield_t_ha: float  = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ConstructionAdvice:
    """Construction guidance based on soil stability"""
    suitability: str                = "Moderate"
    foundation_type: str            = "Raft Foundation"
    foundation_depth_m: float       = 1.5
    precautions: List[str]          = field(default_factory=list)
    estimated_cost_factor: float    = 1.0
    recommendation: str             = ""
    load_bearing_capacity_kPa: int  = 0
    safe_for_multistory: bool       = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CropGrowthStage:
    """Single stage in crop growth simulation"""
    name: str
    days: int
    success_rate: float
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CropSimulation:
    """Full crop growth simulation result"""
    crop: str
    soil_compatibility: int
    stages: List[CropGrowthStage]   = field(default_factory=list)
    estimated_yield_tons_per_ha: float = 0.0
    total_days: int                    = 110
    success_probability: int           = 0
    water_requirement_mm: int          = 0
    fertilizer_cost_factor: float      = 1.0
    recommended_spacing_cm: str        = "30x45"

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "soil_compatibility": self.soil_compatibility,
            "stages": [s.to_dict() for s in self.stages],
            "estimated_yield_tons_per_ha": self.estimated_yield_tons_per_ha,
            "total_days": self.total_days,
            "success_probability": self.success_probability,
            "water_requirement_mm": self.water_requirement_mm,
            "fertilizer_cost_factor": self.fertilizer_cost_factor,
            "recommended_spacing_cm": self.recommended_spacing_cm,
        }


@dataclass
class SoilReport:
    """
    Complete soil analysis report.
    This is the master output object from the SoilModel.
    """
    # Identification
    soil_id: str = ""
    soil_type: str = SoilCategory.UNKNOWN
    soil_code: str = "UNK"
    theme: str = "default"
    description: str = ""
    analyzed_at: str = ""

    # Image / color data
    image_path: str = ""
    avg_rgb: RGBColor = field(default_factory=RGBColor)

    # Physical properties
    texture: str = SoilTexture.LOAM
    ph_range: str = "6.0–7.5"
    ph_value: float = 7.0
    porosity_pct: float = 40.0
    bulk_density_g_cm3: float = 1.3
    organic_carbon_pct: float = 1.5

    # Scores & analytics
    scores: CoreScores = field(default_factory=CoreScores)
    analytics: AdvancedAnalytics = field(default_factory=AdvancedAnalytics)
    nutrients: NutrientProfile = field(default_factory=NutrientProfile)
    crop_recommendations: CropRecommendation = field(default_factory=CropRecommendation)
    construction_advice: ConstructionAdvice = field(default_factory=ConstructionAdvice)

    # Metadata
    district: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_id: Optional[int] = None
    # Predicted soil layers
    layers: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize full report to dict (API-ready)"""
        return {
            # IDs
            "soil_id": self.soil_id,
            "soil_type": self.soil_type,
            "soil_code": self.soil_code,
            "theme": self.theme,
            "description": self.description,
            "analyzed_at": self.analyzed_at,

             "layers": self.layers,

            # Image
            "image_path": self.image_path,
            "avg_rgb": self.avg_rgb.to_dict(),

            # Physical
            "texture": self.texture,
            "ph_range": self.ph_range,
            "ph_value": self.ph_value,
            "porosity_pct": self.porosity_pct,
            "bulk_density": self.bulk_density_g_cm3,
            "organic_carbon_pct": self.organic_carbon_pct,

            # Core scores (flattened for backward compatibility)
            "water_retention": self.scores.water_retention,
            "crop_score": self.scores.crop_score,
            "construction_score": self.scores.construction_score,
            "heat_index": self.scores.heat_index,

            # Advanced analytics (flattened)
            "land_potential_score": self.analytics.land_potential_score,
            "agriculture_roi": self.analytics.agriculture_roi,
            "construction_risk": self.analytics.construction_risk,
            "flood_risk": self.analytics.flood_risk,
            "drought_risk": self.analytics.drought_risk,
            "erosion_risk": self.analytics.erosion_risk,
            "climate_impact": {
                "carbon_sequestration": self.analytics.carbon_sequestration,
                "drought_sensitivity": self.analytics.drought_sensitivity,
                "temperature_rise_effect": self.analytics.temperature_rise_effect,
                "trend": self.analytics.climate_trend,
            },

            # Nested objects
            "nutrients": self.nutrients.to_dict(),
            "crop_recommendations": self.crop_recommendations.to_dict(),
            "construction_advice": self.construction_advice.to_dict(),

            # Geo
            "district": self.district,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SOIL KNOWLEDGE BASE
# ─────────────────────────────────────────────────────────────────────────────

SOIL_KNOWLEDGE_BASE: Dict[str, dict] = {
   SoilCategory.BLACK: {
    "code": "BLK",
    "theme": "black",

    "description": "desc_black_soil",
    "texture": "texture_heavy_clay",
    "ph_range": "ph_range_black",

    "ph_value": 7.2,
    "porosity_pct": 55.0,
    "bulk_density": 1.10,
    "organic_carbon_pct": 2.8,

    "base_scores": {
        "water_retention": 83,
        "crop_score": 88,
        "construction_score": 42,
        "heat_index": 78,
    },

    "nutrients": {
        "nitrogen": 70, "phosphorus": 62, "potassium": 90,
        "organic_matter": 88, "calcium": 92, "magnesium": 80,
        "sulfur": 55, "iron": 50, "zinc": 38,
    },

    "crops": {
        "primary": ["crop_cotton", "crop_sugarcane", "crop_wheat", "crop_jowar"],
        "secondary": ["crop_sunflower", "crop_linseed", "crop_chickpea", "crop_soybean"],
        "avoid": ["crop_groundnut", "crop_potato", "crop_sweet_potato"],
        "season": "season_kharif",
        "irrigation": "irrigation_black",
        "fertilizer": "fertilizer_black",
        "spacing_cm": "spacing_45_60",
        "expected_yield_t_ha": 3.2,
    },

    "construction": {
        "suitability": "construction_poor",
        "foundation": "foundation_deep_pile",
        "foundation_depth_m": 4.0,
        "precautions": [
            "precaution_lime",
            "precaution_no_heavy",
            "precaution_drainage",
            "precaution_geotextile",
            "precaution_crack_monitor"
        ],
        "cost_factor": 1.75,
        "recommendation": "construction_black_recommend",
        "load_bearing_kPa": 80,
        "safe_multistory": False,
    },

    "climate": {
        "carbon_sequestration": "climate_high",
        "drought_sensitivity": "climate_medium",
        "temperature_rise_effect": "climate_moderate",
        "trend": "climate_stable",
    },

    "agriculture_roi_base": 28.5,
},

   SoilCategory.RED: {
    "code": "RED",
    "theme": "red",

    "description": "desc_red_soil",
    "texture": "texture_sandy_loam",
    "ph_range": "ph_range_red",

    "ph_value": 6.0,
    "porosity_pct": 42.0,
    "bulk_density": 1.45,
    "organic_carbon_pct": 0.8,

    "base_scores": {
        "water_retention": 48,
        "crop_score": 62,
        "construction_score": 72,
        "heat_index": 86,
    },

    "nutrients": {
        "nitrogen": 40, "phosphorus": 38, "potassium": 55,
        "organic_matter": 35, "calcium": 45, "magnesium": 40,
        "sulfur": 35, "iron": 92, "zinc": 30,
    },

    "crops": {
        "primary": ["crop_groundnut", "crop_millets", "crop_tobacco", "crop_castor"],
        "secondary": ["crop_ragi", "crop_cowpea", "crop_horsegram", "crop_bajra"],
        "avoid": ["crop_paddy", "crop_sugarcane", "crop_wheat"],
        "season": "season_rabi",
        "irrigation": "irrigation_red",
        "fertilizer": "fertilizer_red",
        "spacing_cm": "spacing_30_45",
        "expected_yield_t_ha": 2.1,
    },

    "construction": {
        "suitability": "construction_good",
        "foundation": "foundation_raft_strip",
        "foundation_depth_m": 1.5,
        "precautions": [
            "precaution_waterproof",
            "precaution_compact",
            "precaution_anticorrosion",
            "precaution_drainage_monsoon"
        ],
        "cost_factor": 1.15,
        "recommendation": "construction_red_recommend",
        "load_bearing_kPa": 200,
        "safe_multistory": True,
    },

    "climate": {
        "carbon_sequestration": "climate_low",
        "drought_sensitivity": "climate_high",
        "temperature_rise_effect": "climate_significant",
        "trend": "climate_degrading",
    },

    "agriculture_roi_base": 18.2,
},
    SoilCategory.CLAY: {
    "code": "YLW",
    "theme": "yellow",

    "description": "desc_clay_soil",
    "texture": "texture_loamy_sand",
    "ph_range": "ph_range_clay",

    "ph_value": 5.8,
    "porosity_pct": 44.0,
    "bulk_density": 1.38,
    "organic_carbon_pct": 1.2,

    "base_scores": {
        "water_retention": 55,
        "crop_score": 58,
        "construction_score": 65,
        "heat_index": 70,
    },

    "nutrients": {
        "nitrogen": 48, "phosphorus": 42, "potassium": 50,
        "organic_matter": 44, "calcium": 38, "magnesium": 42,
        "sulfur": 38, "iron": 72, "zinc": 32,
    },

    "crops": {
        "primary": ["crop_tea", "crop_coffee", "crop_rubber", "crop_cashew"],
        "secondary": ["crop_tapioca", "crop_banana", "crop_pineapple", "crop_coconut"],
        "avoid": ["crop_wheat", "crop_barley", "crop_chickpea"],
        "season": "season_year_round",
        "irrigation": "irrigation_clay",
        "fertilizer": "fertilizer_clay",
        "spacing_cm": "spacing_60_90",
        "expected_yield_t_ha": 2.5,
    },

    "construction": {
        "suitability": "construction_moderate",
        "foundation": "foundation_reinforced_raft",
        "foundation_depth_m": 2.0,
        "precautions": [
            "precaution_compaction_test",
            "precaution_reinforced_raft",
            "precaution_drainage_critical",
            "precaution_leach_test"
        ],
        "cost_factor": 1.30,
        "recommendation": "construction_clay_recommend",
        "load_bearing_kPa": 145,
        "safe_multistory": True,
    },

    "climate": {
        "carbon_sequestration": "climate_medium",
        "drought_sensitivity": "climate_high_moisture",
        "temperature_rise_effect": "climate_moderate_erosion",
        "trend": "climate_at_risk",
    },

    "agriculture_roi_base": 16.8,
},
    SoilCategory.ALLUVIAL: {
    "code": "BRN",
    "theme": "brown",

    "description": "desc_alluvial_soil",
    "texture": "texture_silt_loam",
    "ph_range": "ph_range_alluvial",

    "ph_value": 6.8,
    "porosity_pct": 48.0,
    "bulk_density": 1.25,
    "organic_carbon_pct": 2.2,

    "base_scores": {
        "water_retention": 76,
        "crop_score": 86,
        "construction_score": 68,
        "heat_index": 60,
    },

    "nutrients": {
        "nitrogen": 76, "phosphorus": 72, "potassium": 70,
        "organic_matter": 78, "calcium": 68, "magnesium": 65,
        "sulfur": 55, "iron": 55, "zinc": 48,
    },

    "crops": {
        "primary": ["crop_paddy", "crop_wheat", "crop_sugarcane", "crop_maize"],
        "secondary": ["crop_vegetables", "crop_pulses", "crop_oilseeds", "crop_jute"],
        "avoid": ["crop_tea", "crop_coffee", "crop_rubber", "crop_cashew"],
        "season": "season_alluvial",
        "irrigation": "irrigation_alluvial",
        "fertilizer": "fertilizer_alluvial",
        "spacing_cm": "spacing_20_30",
        "expected_yield_t_ha": 4.8,
    },

    "construction": {
        "suitability": "construction_good",
        "foundation": "foundation_raft_pile",
        "foundation_depth_m": 1.8,
        "precautions": [
            "precaution_water_table",
            "precaution_settlement",
            "precaution_scour",
            "precaution_basement_waterproof"
        ],
        "cost_factor": 1.20,
        "recommendation": "construction_alluvial_recommend",
        "load_bearing_kPa": 160,
        "safe_multistory": True,
    },

    "climate": {
        "carbon_sequestration": "climate_high",
        "drought_sensitivity": "climate_low_moisture",
        "temperature_rise_effect": "climate_low_resilient",
        "trend": "climate_resilient",
    },

    "agriculture_roi_base": 24.3,
},

   SoilCategory.CINDER: {
    "code": "CIN",
    "theme": "gray",

    "description": "desc_cinder_soil",
    "texture": "texture_sandy",
    "ph_range": "ph_range_cinder",

    "ph_value": 6.5,
    "porosity_pct": 60,
    "bulk_density": 1.0,
    "organic_carbon_pct": 1.2,

    "base_scores": {
        "water_retention": 40,
        "crop_score": 45,
        "construction_score": 65,
        "heat_index": 70
    },

    "nutrients": {
        "nitrogen": 35,
        "phosphorus": 30,
        "potassium": 50,
        "organic_matter": 40,
        "calcium": 45,
        "magnesium": 38,
        "sulfur": 30,
        "iron": 55,
        "zinc": 28
    },

    "crops": {
        "primary": ["crop_maize", "crop_millets"],
        "secondary": ["crop_beans", "crop_groundnut"],
        "avoid": ["crop_rice"],
        "season": "season_kharif",
        "irrigation": "irrigation_cinder",
        "fertilizer": "fertilizer_cinder",
        "spacing_cm": "spacing_40_40",
        "expected_yield_t_ha": 1.8
    },

    "construction": {
        "suitability": "construction_moderate",
        "foundation": "foundation_raft",
        "foundation_depth_m": 1.8,
        "precautions": ["precaution_compaction", "precaution_stabilization"],
        "cost_factor": 1.25,
        "recommendation": "construction_cinder_recommend",
        "load_bearing_kPa": 140,
        "safe_multistory": True
    },

    "climate": {
        "carbon_sequestration": "climate_low",
        "drought_sensitivity": "climate_high",
        "temperature_rise_effect": "climate_moderate",
        "trend": "climate_stable"
    },

    "agriculture_roi_base": 15
},

SoilCategory.LATERITE: {
    "code": "LAT",
    "theme": "laterite",

    "description": "desc_laterite_soil",
    "texture": "texture_loam",
    "ph_range": "ph_range_laterite",

    "ph_value": 5.5,
    "porosity_pct": 45,
    "bulk_density": 1.35,
    "organic_carbon_pct": 1.0,

    "base_scores": {
        "water_retention": 50,
        "crop_score": 55,
        "construction_score": 70,
        "heat_index": 75
    },

    "nutrients": {
        "nitrogen": 40,
        "phosphorus": 35,
        "potassium": 45,
        "organic_matter": 40,
        "calcium": 42,
        "magnesium": 38,
        "sulfur": 35,
        "iron": 80,
        "zinc": 30
    },

    "crops": {
        "primary": ["crop_tea", "crop_coffee"],
        "secondary": ["crop_cashew", "crop_rubber"],
        "avoid": ["crop_wheat"],
        "season": "season_year_round",
        "irrigation": "irrigation_laterite",
        "fertilizer": "fertilizer_laterite",
        "spacing_cm": "spacing_60_60",
        "expected_yield_t_ha": 2.3
    },

    "construction": {
        "suitability": "construction_moderate",
        "foundation": "foundation_raft",
        "foundation_depth_m": 2,
        "precautions": ["precaution_drainage_required"],
        "cost_factor": 1.2,
        "recommendation": "construction_laterite_recommend",
        "load_bearing_kPa": 150,
        "safe_multistory": True
    },

    "climate": {
        "carbon_sequestration": "climate_medium",
        "drought_sensitivity": "climate_medium",
        "temperature_rise_effect": "climate_moderate",
        "trend": "climate_stable"
    },

    "agriculture_roi_base": 17
},

SoilCategory.PEAT: {
    "code": "PET",
    "theme": "peat",

    "description": "desc_peat_soil",
    "texture": "texture_silt_loam",
    "ph_range": "ph_range_peat",

    "ph_value": 4.8,
    "porosity_pct": 65,
    "bulk_density": 0.9,
    "organic_carbon_pct": 8.0,

    "base_scores": {
        "water_retention": 90,
        "crop_score": 50,
        "construction_score": 30,
        "heat_index": 60
    },

    "nutrients": {
        "nitrogen": 60,
        "phosphorus": 40,
        "potassium": 45,
        "organic_matter": 95,
        "calcium": 30,
        "magnesium": 35,
        "sulfur": 45,
        "iron": 50,
        "zinc": 32
    },

    "crops": {
        "primary": ["crop_rice"],
        "secondary": ["crop_vegetables"],
        "avoid": ["crop_cotton"],
        "season": "season_wet",
        "irrigation": "irrigation_peat",
        "fertilizer": "fertilizer_peat",
        "spacing_cm": "spacing_25_25",
        "expected_yield_t_ha": 2.0
    },

    "construction": {
        "suitability": "construction_poor",
        "foundation": "foundation_deep_pile",
        "foundation_depth_m": 4,
        "precautions": ["precaution_drainage_required"],
        "cost_factor": 1.8,
        "recommendation": "construction_peat_recommend",
        "load_bearing_kPa": 60,
        "safe_multistory": False
    },

    "climate": {
        "carbon_sequestration": "climate_very_high",
        "drought_sensitivity": "climate_low",
        "temperature_rise_effect": "climate_low",
        "trend": "climate_sensitive"
    },

    "agriculture_roi_base": 14
},

SoilCategory.YELLOW: {
    "code": "YLW",
    "theme": "yellow",

    "description": "desc_yellow_soil",
    "texture": "texture_loam",
    "ph_range": "ph_range_yellow",

    "ph_value": 6.0,
    "porosity_pct": 46,
    "bulk_density": 1.32,
    "organic_carbon_pct": 1.4,

    "base_scores": {
        "water_retention": 55,
        "crop_score": 60,
        "construction_score": 66,
        "heat_index": 70
    },

    "nutrients": {
        "nitrogen": 45,
        "phosphorus": 42,
        "potassium": 50,
        "organic_matter": 48,
        "calcium": 40,
        "magnesium": 44,
        "sulfur": 38,
        "iron": 65,
        "zinc": 35
    },

    "crops": {
        "primary": ["crop_tea", "crop_coffee"],
        "secondary": ["crop_cashew", "crop_banana"],
        "avoid": ["crop_wheat"],
        "season": "season_year_round",
        "irrigation": "irrigation_yellow",
        "fertilizer": "fertilizer_yellow",
        "spacing_cm": "spacing_60_60",
        "expected_yield_t_ha": 2.4
    },

    "construction": {
        "suitability": "construction_moderate",
        "foundation": "foundation_raft",
        "foundation_depth_m": 2,
        "precautions": ["precaution_drainage_needed"],
        "cost_factor": 1.2,
        "recommendation": "construction_yellow_recommend",
        "load_bearing_kPa": 150,
        "safe_multistory": True
    },

    "climate": {
        "carbon_sequestration": "climate_medium",
        "drought_sensitivity": "climate_medium",
        "temperature_rise_effect": "climate_moderate",
        "trend": "climate_stable"
    },

    "agriculture_roi_base": 18
}
}


# ─────────────────────────────────────────────────────────────────────────────
# SOIL CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

class SoilAIModel:
    def __init__(self, model_path="soil_model.h5"):
        import tensorflow as tf
        import h5py
        import json
        from tensorflow.keras.models import load_model

        # 1. மாடல் கன்பிக் (Config) திருத்தம்
        try:
            with h5py.File(model_path, 'r+') as f:
                if 'model_config' in f.attrs:
                    # மெட்டாடேட்டாவிலிருந்து JSON-ஐ எடுக்கிறோம்
                    model_config_raw = f.attrs['model_config']
                    if isinstance(model_config_raw, bytes):
                        model_config_raw = model_config_raw.decode('utf-8')
                    
                    config = json.loads(model_config_raw)
                    
                    def patch_input_layer(obj):
                        if isinstance(obj, dict):
                            # Dense லேயர் பிரச்சனையை சரி செய்கிறோம்
                            obj.pop('quantization_config', None)
                            
                            # InputLayer-ல் 'shape' அல்லது 'batch_shape' இல்லைனா சேர்க்கிறோம்
                            if obj.get('class_name') == 'InputLayer':
                                layer_config = obj.get('config', {})
                                if 'batch_shape' not in layer_config and 'shape' not in layer_config:
                                    layer_config['batch_shape'] = [None, 224, 224, 3]
                                    obj['config'] = layer_config
                            
                            # Recursive-ஆக எல்லா இடத்திலும் தேடுகிறோம்
                            for key in obj:
                                patch_input_layer(obj[key])
                        elif isinstance(obj, list):
                            for item in obj:
                                patch_input_layer(item)

                    patch_input_layer(config)
                    # திருத்தப்பட்ட கன்பிக்கை மீண்டும் ஃபைலில் எழுதுகிறோம்
                    f.attrs['model_config'] = json.dumps(config).encode('utf-8')
            print("✓ Soil model patched for InputLayer and Dense layers.")
        except Exception as e:
            print(f"! Pre-processing failed: {e}")

        # 2. இப்போது மாடலை லோடு செய்கிறோம்
        try:
            self.model = load_model(model_path, compile=False)
        except Exception as e:
            print(f"Loading failed again: {e}")
            raise e

        self.classes = [
          "Alluvial Soil",
          "Black Soil",
          "Cinder Soil",
          "Clay Soil",
          "Laterite Soil",
          "Peat Soil",
          "Red Soil",
          "Yellow Soil"
        ]

    def predict(self, image_path):

        img = Image.open(image_path).convert("RGB")
        img = img.resize((224,224))

        arr = np.array(img) / 255.0
        arr = np.expand_dims(arr, axis=0)

        pred = self.model.predict(arr)

        idx = np.argmax(pred)

        soil = self.classes[idx]
        confidence = float(np.max(pred))

        return soil, confidence

class SoilClassifier:
    """
    Classifies soil based on RGB color analysis.
    Uses a multi-rule decision engine with confidence scoring.
    """

    CLASSIFICATION_RULES = [
("Peat Soil", lambda c: c.brightness < 0.20, 10),
("Black Soil", lambda c: c.brightness < 0.30, 9),
("Red Soil", lambda c: c.redness_ratio > 1.4, 8),
("Laterite Soil", lambda c: c.redness_ratio > 1.2 and c.brightness > 0.35, 7),
("Clay Soil", lambda c: c.yellowness_ratio > 1.7, 6),
("Yellow Soil", lambda c: c.yellowness_ratio > 1.9, 5),
("Cinder Soil", lambda c: c.saturation < 0.2, 4),
("Alluvial Soil", lambda c: True, 1),
    ]

    @classmethod
    def classify(cls, color: RGBColor) -> Tuple[str, float]:
        """
        Returns (soil_type, confidence_score 0–1).
        Evaluates all rules by priority and picks the first matching.
        """
        matched = None
        confidence = 0.5

        for name, rule, priority in sorted(cls.CLASSIFICATION_RULES, key=lambda x: -x[2]):
            if rule(color):
                matched = name
                confidence = cls._compute_confidence(color, name)
                break

        return matched or SoilCategory.UNKNOWN, round(confidence, 3)

    @staticmethod
    def _compute_confidence(color: RGBColor, soil_type: str) -> float:
        """Estimate confidence by how far the color is from ideal centroids"""
        ideal_centroids = {
            "Black Soil":          RGBColor(30,  28,  25),
            "Red Soil":            RGBColor(160, 60,  40),
            "Clay Soil":         RGBColor(180, 150, 60),
            "Alluvial Soil": RGBColor(120, 90,  55),
        }
        ideal = ideal_centroids.get(soil_type)
        if not ideal:
            return 0.5

        distance = math.sqrt(
            (color.r - ideal.r) ** 2 +
            (color.g - ideal.g) ** 2 +
            (color.b - ideal.b) ** 2
        )
        max_possible = math.sqrt(3 * 255**2)
        confidence = 1.0 - (distance / max_possible)
        return max(0.3, min(0.99, confidence))

    @classmethod
    def all_scores(cls, color: RGBColor) -> List[Tuple[str, float]]:
        """Return confidence scores for all soil types (for UI visualization)"""
        results = []
        for name, rule, _ in cls.CLASSIFICATION_RULES:
            if name == "Alluvial Soil":
                conf = cls._compute_confidence(color, name)
            elif rule(color):
                conf = cls._compute_confidence(color, name)
            else:
                conf = cls._compute_confidence(color, name) * 0.4
            results.append((name, round(conf, 3)))
        return sorted(results, key=lambda x: -x[1])


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class ScoringEngine:
    """
    Computes all numeric scores from soil knowledge base.
    Applies realistic small variance and bounds all values to [0, 100].
    """

    SCORE_VARIANCE = 5   # ±5 points per analysis

    @classmethod
    def compute_core_scores(cls, soil_type: str, seed: Optional[int] = None) -> CoreScores:
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, SOIL_KNOWLEDGE_BASE[SoilCategory.ALLUVIAL])
        base = kb["base_scores"]
        rng = random.Random(seed) if seed is not None else random
        v = cls.SCORE_VARIANCE

        return CoreScores(
            water_retention    = cls._clamp(base["water_retention"]    + rng.randint(-v, v)),
            crop_score         = cls._clamp(base["crop_score"]         + rng.randint(-v, v)),
            construction_score = cls._clamp(base["construction_score"] + rng.randint(-v, v)),
            heat_index         = cls._clamp(base["heat_index"]         + rng.randint(-v, v)),
        )

    @classmethod
    def compute_land_potential(cls, scores: CoreScores) -> int:
        """
        Composite land potential score:
        40% crop · 30% water · 20% construction · 10% inverse-heat
        """
        score = (
            scores.crop_score         * 0.40 +
            scores.water_retention    * 0.30 +
            scores.construction_score * 0.20 +
            (100 - scores.heat_index) * 0.10
        )
        return cls._clamp(round(score))

    @classmethod
    def compute_agriculture_roi(cls, soil_type: str, scores: CoreScores) -> float:
        """Estimate agriculture ROI (%) based on soil type + scores"""
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, {})
        base_roi = kb.get("agriculture_roi_base", 18.0)
        score_modifier = ((scores.crop_score + scores.water_retention) / 200) * 12 - 6
        return round(base_roi + score_modifier, 1)

    @classmethod
    def compute_construction_risk(cls, score: int) -> str:
        if score >= 75: return RiskLevel.LOW
        if score >= 55: return RiskLevel.MEDIUM
        if score >= 35: return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    @classmethod
    def compute_flood_risk(cls, water_retention: int, construction_score: int) -> str:
        risk_score = water_retention * 0.60 + (100 - construction_score) * 0.40
        if risk_score < 38:  return RiskLevel.LOW
        if risk_score < 55:  return RiskLevel.MEDIUM
        if risk_score < 72:  return RiskLevel.HIGH
        return RiskLevel.VERY_HIGH

    @classmethod
    def compute_drought_risk(cls, water_retention: int) -> str:
        if water_retention >= 70: return RiskLevel.LOW
        if water_retention >= 50: return RiskLevel.MEDIUM
        if water_retention >= 30: return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    @classmethod
    def compute_erosion_risk(cls, water_retention: int, heat_index: int) -> str:
        risk = (heat_index * 0.5) + ((100 - water_retention) * 0.5)
        if risk < 35: return RiskLevel.LOW
        if risk < 55: return RiskLevel.MEDIUM
        if risk < 70: return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    @staticmethod
    def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
        return max(lo, min(hi, value))


# ─────────────────────────────────────────────────────────────────────────────
# NUTRIENT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class NutrientEngine:
    """Build NutrientProfile from knowledge base with realistic variation"""

    VARIANCE = 6

    @classmethod
    def build_profile(cls, soil_type: str, seed: Optional[int] = None) -> NutrientProfile:
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, SOIL_KNOWLEDGE_BASE[SoilCategory.ALLUVIAL])
        n = kb["nutrients"]
        rng = random.Random(seed) if seed is not None else random
        v = cls.VARIANCE

        def jitter(val: int) -> int:
            return max(0, min(100, val + rng.randint(-v, v)))

        return NutrientProfile(
            nitrogen       = jitter(n["nitrogen"]),
            phosphorus     = jitter(n["phosphorus"]),
            potassium      = jitter(n["potassium"]),
            organic_matter = jitter(n["organic_matter"]),
            calcium        = jitter(n["calcium"]),
            magnesium      = jitter(n["magnesium"]),
            sulfur         = jitter(n["sulfur"]),
            iron           = jitter(n["iron"]),
            zinc           = jitter(n["zinc"]),
        )


# ─────────────────────────────────────────────────────────────────────────────
# CONSTRUCTION ADVISOR
# ─────────────────────────────────────────────────────────────────────────────

class ConstructionAdvisor:
    """Generate construction advice from soil type knowledge base"""

    @classmethod
    def get_advice(cls, soil_type: str, construction_score: int) -> ConstructionAdvice:
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, SOIL_KNOWLEDGE_BASE[SoilCategory.ALLUVIAL])
        c = kb["construction"]

        return ConstructionAdvice(
            suitability             = c["suitability"],
            foundation_type         = c["foundation"],
            foundation_depth_m      = c["foundation_depth_m"],
            precautions             = c["precautions"],
            estimated_cost_factor   = c["cost_factor"],
            recommendation          = c["recommendation"],
            load_bearing_capacity_kPa = c["load_bearing_kPa"],
            safe_for_multistory     = c["safe_multistory"],
        )


# ─────────────────────────────────────────────────────────────────────────────
# CROP ADVISOR
# ─────────────────────────────────────────────────────────────────────────────

class CropAdvisor:
    """Generate crop recommendations and growth simulations"""

    CROP_WATER_NEEDS: Dict[str, int] = {
        "Wheat":     450, "Cotton":    700, "Sugarcane": 1800, "Paddy":    1200,
        "Groundnut": 500, "Millets":   400, "Maize":     600, "Sunflower": 600,
        "Tea":       1400,"Coffee":    1200,"Rubber":    2000, "Cashew":   900,
        "Ragi":      350, "Jowar":     450, "Bajra":     350, "Soybean":  600,
    }

    CROP_SPACING: Dict[str, str] = {
        "Wheat": "10×15",   "Cotton":    "90×60",   "Sugarcane": "75×30",
        "Paddy": "20×15",   "Groundnut": "30×10",   "Millets":   "45×15",
        "Maize": "60×25",   "Sunflower": "60×30",   "Tea":       "120×60",
        "Coffee":"240×240", "Rubber":    "600×300", "Cashew":    "800×800",
    }

    @classmethod
    def get_recommendations(cls, soil_type: str) -> CropRecommendation:
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, SOIL_KNOWLEDGE_BASE[SoilCategory.ALLUVIAL])
        cr = kb["crops"]
        return CropRecommendation(
            primary             = cr["primary"],
            secondary           = cr["secondary"],
            avoid               = cr["avoid"],
            season              = cr["season"],
            irrigation          = cr["irrigation"],
            fertilizer          = cr["fertilizer"],
            spacing_cm          = cr.get("spacing_cm", "30×30"),
            expected_yield_t_ha = cr.get("expected_yield_t_ha", 2.5),
        )

    @classmethod
    def simulate_growth(cls, crop: str, crop_score: int, water_retention: int) -> CropSimulation:
        """Simulate crop growth stages for selected crop + soil scores"""
        compatibility = round((crop_score * 0.6 + water_retention * 0.4))

        STAGE_DEFS = [
            ("Seed Germination",  7,  compatibility + 12, "Seeds absorb water and sprout."),
            ("Seedling Stage",   21,  compatibility +  6, "Root system develops."),
            ("Vegetative Growth",45,  compatibility +  0, "Leaf and stem rapid expansion."),
            ("Flowering",        65,  compatibility -  5, "Reproductive organs form."),
            ("Grain/Fruit Fill", 88,  compatibility - 10, "Energy reserves fill fruit/grain."),
            ("Harvest Ready",   110,  compatibility - 16, "Crop reaches maturity."),
        ]

        stages = [
            CropGrowthStage(
                name         = name,
                days         = days,
                success_rate = max(5, min(100, rate)),
                description  = desc,
            )
            for name, days, rate, desc in STAGE_DEFS
        ]

        estimated_yield = (compatibility / 100) * 5.0 * cls._yield_multiplier(crop)
        water_need = cls.CROP_WATER_NEEDS.get(crop, 550)

        return CropSimulation(
            crop                        = crop,
            soil_compatibility          = compatibility,
            stages                      = stages,
            estimated_yield_tons_per_ha = round(estimated_yield, 2),
            total_days                  = 110,
            success_probability         = compatibility,
            water_requirement_mm        = water_need,
            fertilizer_cost_factor      = round(1.5 - compatibility / 200, 2),
            recommended_spacing_cm      = cls.CROP_SPACING.get(crop, "45×30"),
        )

    @staticmethod
    def _yield_multiplier(crop: str) -> float:
        multipliers = {
            "Sugarcane": 12.0, "Paddy": 1.8, "Wheat": 1.6, "Maize": 1.5,
            "Cotton":    0.5,  "Tea":   0.8, "Coffee": 0.7, "Rubber": 0.4,
        }
        return multipliers.get(crop, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# ID GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class SoilIDGenerator:
    """
    Generates unique Soil IDs.
    Format: SV360-<SOILCODE>-<RANDOM4DIGITS>
    e.g.   SV360-BLK-4729
    """

    @staticmethod
    def generate(soil_code: str, image_path: str = "") -> str:
        # Seed RNG with image path hash for reproducibility per image
        if image_path:
            seed = int(hashlib.md5(image_path.encode()).hexdigest()[:8], 16) % 10000
        else:
            seed = random.randint(1000, 9999)
        return f"SV360-{soil_code}-{seed:04d}"


# ─────────────────────────────────────────────────────────────────────────────
# IMAGE READER
# ─────────────────────────────────────────────────────────────────────────────

class ImageColorReader:
    """
    Reads average RGB from an image file.
    Uses Pillow/NumPy when available, falls back gracefully.
    """

    @staticmethod
    def read(image_path: str) -> RGBColor:
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(image_path).convert("RGB")
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            arr = np.array(img, dtype=np.float32)

            # Crop centre 80% to reduce background influence
            h, w = arr.shape[:2]
            pad_h, pad_w = h // 10, w // 10
            arr = arr[pad_h:-pad_h or None, pad_w:-pad_w or None]

            r, g, b = int(arr[:,:,0].mean()), int(arr[:,:,1].mean()), int(arr[:,:,2].mean())
            return RGBColor(r, g, b)

        except ImportError:
            return ImageColorReader._fallback(image_path)
        except Exception:
            return ImageColorReader._fallback(image_path)

    @staticmethod
    def _fallback(image_path: str) -> RGBColor:
        """Deterministic fallback using filename hash"""
        seed = sum(ord(c) for c in os.path.basename(image_path))
        rng = random.Random(seed)
        return RGBColor(
            r = rng.randint(50, 200),
            g = rng.randint(35, 140),
            b = rng.randint(20, 90),
        )


# ─────────────────────────────────────────────────────────────────────────────
# MASTER SOIL MODEL
# ─────────────────────────────────────────────────────────────────────────────

class SoilModel:
    """
    ╔═══════════════════════════════════════════════════════╗
    ║          SOIL VISION 360 — Master Soil Model          ║
    ║                                                       ║
    ║  High-level orchestrator.  Call SoilModel.analyze()  ║
    ║  with an image path to get a full SoilReport.        ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self):
        self.classifier  = SoilClassifier()
        self.scorer      = ScoringEngine()
        self.nutrienter  = NutrientEngine()
        self.constructor = ConstructionAdvisor()
        self.cropper     = CropAdvisor()
        self.id_gen      = SoilIDGenerator()
        self.reader      = ImageColorReader()
        model_path = os.path.join(os.path.dirname(__file__), "soil_model.h5")
        self.ai_model = SoilAIModel(model_path)

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        image_path: str,
        user_id: Optional[int] = None,
    ) -> SoilReport:
        """
        Full pipeline:
        image → RGB → classify → score → nutrients → advice → report
        """
        # 1. Read image colour
        color = self.reader.read(image_path)

        # 2. Classify
        try:
            soil_type, confidence = self.ai_model.predict(image_path)
        except:
            soil_type, confidence = self.classifier.classify(color)

        layers = get_soil_layers(soil_type)

        # 3. Fetch knowledge base entry
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, SOIL_KNOWLEDGE_BASE[SoilCategory.ALLUVIAL])

        # 4. Compute scores (use image hash as seed for reproducibility)
        seed = int(hashlib.md5(os.path.basename(image_path).encode()).hexdigest()[:4], 16)
        scores = self.scorer.compute_core_scores(soil_type, seed=seed)

        # 5. Advanced analytics
        land_potential  = self.scorer.compute_land_potential(scores)
        agriculture_roi = self.scorer.compute_agriculture_roi(soil_type, scores)
        climate         = kb["climate"]

        analytics = AdvancedAnalytics(
            land_potential_score    = land_potential,
            agriculture_roi         = agriculture_roi,
            construction_risk       = self.scorer.compute_construction_risk(scores.construction_score),
            flood_risk              = self.scorer.compute_flood_risk(scores.water_retention, scores.construction_score),
            drought_risk            = self.scorer.compute_drought_risk(scores.water_retention),
            erosion_risk            = self.scorer.compute_erosion_risk(scores.water_retention, scores.heat_index),
            carbon_sequestration    = climate["carbon_sequestration"],
            drought_sensitivity     = climate["drought_sensitivity"],
            temperature_rise_effect = climate["temperature_rise_effect"],
            climate_trend           = climate["trend"],
            estimated_cost_factor   = kb["construction"]["cost_factor"],
        )

        # 6. Nutrients
        nutrients = self.nutrienter.build_profile(soil_type, seed=seed)

        # 7. Crop recommendations
        crop_recs = self.cropper.get_recommendations(soil_type)

        # 8. Construction advice
        const_advice = self.constructor.get_advice(soil_type, scores.construction_score)

        # 9. Generate Soil ID
        soil_id = self.id_gen.generate(kb["code"], image_path)

        # 10. Assemble report
        report = SoilReport(
            soil_id              = soil_id,
            soil_type            = soil_type,
            soil_code            = kb["code"],
            theme                = kb["theme"],
            description          = kb["description"],
            analyzed_at          = datetime.utcnow().isoformat() + "Z",
            image_path           = f"/static/uploads/{os.path.basename(image_path)}",
            avg_rgb              = color,
            texture              = kb["texture"],
            ph_range             = kb["ph_range"],
            ph_value             = kb["ph_value"],
            porosity_pct         = kb["porosity_pct"],
            bulk_density_g_cm3   = kb["bulk_density"],
            organic_carbon_pct   = kb["organic_carbon_pct"],
            scores               = scores,
            analytics            = analytics,
            nutrients            = nutrients,
            crop_recommendations = crop_recs,
            construction_advice  = const_advice,
            user_id              = user_id,
            layers               = layers,
        )

        return report

    def analyze_dict(self, image_path: str, **kwargs) -> dict:
        """Convenience: returns serializable dict instead of SoilReport"""
        report = self.analyze(image_path, **kwargs)
        return report.to_dict()

    def simulate_crop(
        self,
        crop: str,
        crop_score: int,
        water_retention: int
    ) -> dict:
        """Run crop growth simulation and return dict"""
        sim = self.cropper.simulate_growth(crop, crop_score, water_retention)
        return sim.to_dict()

    def classify_only(self, image_path: str) -> dict:
        """Fast classification only — no full report"""
        color = self.reader.read(image_path)
        soil_type, confidence = self.classifier.classify(color)
        all_scores = self.classifier.all_scores(color)
        kb = SOIL_KNOWLEDGE_BASE.get(soil_type, {})
        return {
            "soil_type": soil_type,
            "confidence": confidence,
            "avg_rgb": color.to_dict(),
            "soil_code": kb.get("code", "UNK"),
            "theme": kb.get("theme", "default"),
            "all_confidence_scores": [
                {"type": t, "confidence": c} for t, c in all_scores
            ],
        }

    def get_chatbot_response(
        self,
        message: str,
        soil_type: str,
        construction_score: int = 50,
        crop_score: int = 50,
    ) -> str:
        """
        Rule-based AI chatbot engine.
        Returns a rich text response based on message intent + soil context.
        """
        msg = message.lower()
        kb  = SOIL_KNOWLEDGE_BASE.get(soil_type, {})
        cr  = kb.get("crops", {})
        cc  = kb.get("construction", {})

        # Intent detection
        intents = {
            "crops":        any(w in msg for w in ["crop","plant","grow","farm","agricult","cultivat","harvest"]),
            "irrigation":   any(w in msg for w in ["water","irrigat","moisture","rain","flood","drip"]),
            "construction": any(w in msg for w in ["build","construct","house","found","structur","cement","concrete"]),
            "fertilizer":   any(w in msg for w in ["fertil","nutrient","compost","manure","npk","organic","nitrogen"]),
            "risk":         any(w in msg for w in ["risk","danger","hazard","safe","crack","flood","drought"]),
            "roi":          any(w in msg for w in ["roi","profit","money","invest","return","earn","income"]),
            "climate":      any(w in msg for w in ["climat","carbon","temperature","global warming","rain","weather"]),
            "ph":           any(w in msg for w in ["ph","acid","alkalin","lime","basic"]),
            "texture":      any(w in msg for w in ["texture","Clay","sand","silt","loam","soil particle"]),
            "greeting":     any(w in msg for w in ["hello","hi","hey","help","start","what can"]),
        }

        if not soil_type:
            return (
                "👋 Welcome to **SoilBot 360**! Please upload and analyze a soil image first, "
                "then I can answer specific questions about **crops, irrigation, construction, "
                "fertilizers, ROI**, and **climate risks** for your soil."
            )

        if intents["greeting"]:
            return (
                f"Hello! I'm analyzing your **{soil_type}** 🌱\n\n"
                f"Here's what I can help with:\n"
                f"• 🌾 Best crops for your soil\n"
                f"• 💧 Irrigation scheduling\n"
                f"• 🏗️ Construction advice\n"
                f"• 🧪 Fertilizer plan\n"
                f"• 💰 Agriculture ROI\n"
                f"• ⚠️ Risk assessment\n\n"
                f"What would you like to know?"
            )

        if intents["crops"]:
            primary   = ", ".join(cr.get("primary", []))
            secondary = ", ".join(cr.get("secondary", []))
            avoid_    = ", ".join(cr.get("avoid", [])) or "None"
            return (
                f"🌾 **Crop Recommendations for {soil_type}:**\n\n"
                f"**Primary crops:** {primary}\n"
                f"**Secondary crops:** {secondary}\n"
                f"**Avoid:** {avoid_}\n\n"
                f"**Best season:** {cr.get('season', 'Year-round')}\n"
                f"**Expected yield:** {cr.get('expected_yield_t_ha', 2.5)} tons/hectare"
            )

        if intents["irrigation"]:
            return (
                f"💧 **Irrigation Guide for {soil_type}:**\n\n"
                f"{cr.get('irrigation', 'Standard irrigation recommended.')}\n\n"
                f"**Water Retention:** {kb.get('base_scores', {}).get('water_retention', 60)}% capacity\n"
                f"**Tip:** Monitor soil moisture at 10–15 cm depth before each irrigation cycle."
            )

        if intents["construction"]:
            s = construction_score
            risk_text = ScoringEngine.compute_construction_risk(s)
            return (
                f"🏗️ **Construction Analysis for {soil_type}:**\n\n"
                f"**Stability Score:** {s}/100 → Risk: **{risk_text}**\n"
                f"**Foundation:** {cc.get('foundation', 'Standard')}\n"
                f"**Load Bearing:** {cc.get('load_bearing_kPa', 150)} kPa\n"
                f"**Cost Factor:** {cc.get('cost_factor', 1.0)}× baseline\n\n"
                f"💡 {cc.get('recommendation', 'Consult a civil engineer.')}"
            )

        if intents["fertilizer"]:
            return (
                f"🧪 **Fertilizer Plan for {soil_type}:**\n\n"
                f"{cr.get('fertilizer', 'Balanced NPK recommended.')}\n\n"
                f"**pH Range:** {kb.get('ph_range', '6–7')}\n"
                f"**Organic Carbon:** {kb.get('organic_carbon_pct', 1.5)}%\n"
                f"💡 Always do a soil test before bulk fertilizer purchase."
            )

        if intents["risk"]:
            c_risk = ScoringEngine.compute_construction_risk(construction_score)
            d_risk = ScoringEngine.compute_drought_risk(kb.get("base_scores", {}).get("water_retention", 60))
            return (
                f"⚠️ **Risk Assessment for {soil_type}:**\n\n"
                f"• Construction Risk: **{c_risk}**\n"
                f"• Drought Risk:      **{d_risk}**\n"
                f"• Flood Risk:        based on seasonal rainfall\n\n"
                f"**Climate Trend:** {kb.get('climate', {}).get('trend', 'Monitor regularly')}"
            )

        if intents["roi"]:
            roi_base = kb.get("agriculture_roi_base", 20)
            return (
                f"💰 **Agriculture ROI for {soil_type}:**\n\n"
                f"**Base ROI:** ~{roi_base}% annually\n"
                f"**Crop Score Boost:** up to +{round(crop_score/20, 1)}% with optimal crops\n\n"
                f"**Best ROI crops:** {', '.join(cr.get('primary', [])[:2])}\n"
                f"💡 Crop rotation + drip irrigation can improve ROI by 15–20%."
            )

        if intents["climate"]:
            cl = kb.get("climate", {})
            return (
                f"🌍 **Climate Impact for {soil_type}:**\n\n"
                f"• Carbon Sequestration: {cl.get('carbon_sequestration', '—')}\n"
                f"• Drought Sensitivity:  {cl.get('drought_sensitivity', '—')}\n"
                f"• Temp Rise Effect:     {cl.get('temperature_rise_effect', '—')}\n\n"
                f"**Forecast:** {cl.get('trend', '—')}"
            )

        if intents["ph"]:
            return (
                f"⚗️ **pH Information for {soil_type}:**\n\n"
                f"**Optimal pH Range:** {kb.get('ph_range', '6.0–7.5')}\n"
                f"**Current Estimated pH:** {kb.get('ph_value', 7.0)}\n\n"
                f"Soil pH controls nutrient availability. Values outside the optimal "
                f"range lock out key nutrients even if they are physically present in the soil."
            )

        if intents["texture"]:
            return (
                f"🪨 **Texture Profile for {soil_type}:**\n\n"
                f"**Texture Class:** {kb.get('texture', 'Loam')}\n"
                f"**Bulk Density:** {kb.get('bulk_density', 1.3)} g/cm³\n"
                f"**Porosity:** {kb.get('porosity_pct', 45)}%\n"
                f"**Organic Carbon:** {kb.get('organic_carbon_pct', 1.5)}%\n\n"
                f"Texture determines drainage, aeration, and root penetration ability."
            )

        # Generic fallback
        return (
            f"Your **{soil_type}** is ready for analysis. "
            f"Ask me about crops 🌾, irrigation 💧, construction 🏗️, "
            f"fertilizers 🧪, ROI 💰, climate 🌍, pH ⚗️, or soil texture 🪨!"
        )


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL HELPERS (backward-compatible API for blueprints/api.py)
# ─────────────────────────────────────────────────────────────────────────────

_default_model = SoilModel()


def analyze_soil_image(image_path: str, **kwargs) -> dict:
    """Module-level helper — used by blueprints/api.py"""
    return _default_model.analyze_dict(image_path, **kwargs)


def get_crop_growth_simulation(crop: str, crop_score: int, water_retention: int) -> dict:
    """Module-level helper — used by blueprints/api.py"""
    return _default_model.simulate_crop(crop, crop_score, water_retention)


def classify_soil_image(image_path: str) -> dict:
    """Quick classify without full report"""
    return _default_model.classify_only(image_path)


def get_chatbot_response(message: str, soil_type: str, **kwargs) -> str:
    """Module-level chatbot — used by blueprints/api.py"""
    return _default_model.get_chatbot_response(message, soil_type, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  SOIL VISION 360 — Soil Model Self-Test")
    print("=" * 60)

    model = SoilModel()

    # Test each soil type via forced RGB
    test_cases = [
        ("Black Soil",          RGBColor(25, 22, 20)),
        ("Red Soil",            RGBColor(160, 55, 38)),
        ("Clay Soil",         RGBColor(175, 148, 55)),
        ("Alluvial Soil", RGBColor(118, 88, 52)),
    ]

    for expected_type, color in test_cases:
        detected, conf = SoilClassifier.classify(color)
        match = "✓" if detected == expected_type else "✗"
        print(f"\n{match} {expected_type}")
        print(f"  RGB={color.to_dict()['hex']}  Detected={detected}  Confidence={conf:.2%}")

    # Simulate analysis with a fake path
    print("\n" + "─" * 60)
    print("Running full analysis on simulated path...")
    result = analyze_soil_image("/fake/path/soil_sample.jpg")
    print(f"  Soil Type : {result['soil_type']}")
    print(f"  Soil ID   : {result['soil_id']}")
    print(f"  Crop Score: {result['crop_score']}%")
    print(f"  Land Pot. : {result['land_potential_score']}%")
    print(f"  Agri ROI  : {result['agriculture_roi']}%")

    print("\n✅ Soil Model self-test complete.\n")