import json
import os

def load_lang(lang):
    path = os.path.join("static", "lang", f"{lang}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def translate_analysis(data, lang):

    translations = load_lang(lang)

    def t(val):
        if not isinstance(val, str):
             return val

        key = val.strip()

    # 🔥 direct match
        if key in translations:
             return translations[key]

    # 🔥 case variations
        for k in [key.lower(), key.title(), key.upper()]:
            if k in translations:
              return translations[k]

    # 🔥 underscore ↔ space
        if key.replace("_", " ") in translations:
            return translations[key.replace("_", " ")]

        if key.replace(" ", "_") in translations:
             return translations[key.replace(" ", "_")]

    # 🔥 PREFIX HANDLING (VERY IMPORTANT)
    # climate_medium → climate_medium
    # foundation_reinforced_raft → foundation_reinforced_raft

        parts = key.split("_")
        if len(parts) > 1:
          for i in range(len(parts)):
            sub = "_".join(parts[i:])
            if sub in translations:
                return translations[sub]

        return key  # fallback

    # 🔹 Soil type
    if "soil_type" in data:
        data["soil_type"] = t(data["soil_type"])

    # 🔹 Description
    if "description" in data:
        data["description"] = t(data["description"])

    # 🔹 Texture & pH
    if "texture" in data:
        data["texture"] = t(data["texture"])

    if "ph_range" in data:
        data["ph_range"] = t(data["ph_range"])

    # 🔹 Risks
    for key in ["construction_risk", "flood_risk", "drought_risk", "erosion_risk"]:
        if key in data:
            data[key] = t(data[key])

    # 🔹 Climate
    if "climate_impact" in data:
        for k, v in data["climate_impact"].items():
            if isinstance(v, str):
                data["climate_impact"][k] = t(v)

    # 🔹 Construction advice
    if "construction_advice" in data:
        for key, val in data["construction_advice"].items():
            if isinstance(val, str):
                data["construction_advice"][key] = t(val)

    # 🔹 Crop recommendations
    if "crop_recommendations" in data:
        for k in ["primary", "secondary", "avoid"]:
            data["crop_recommendations"][k] = [
                t(c) for c in data["crop_recommendations"].get(k, [])
            ]

        if "season" in data["crop_recommendations"]:
            data["crop_recommendations"]["season"] = t(data["crop_recommendations"]["season"])

        if "irrigation" in data["crop_recommendations"]:
            data["crop_recommendations"]["irrigation"] = t(data["crop_recommendations"]["irrigation"])

    # 🔹 Layers
    if "layers" in data:
      for layer in data["layers"]:
        if "layer" in layer:
            layer["original"] = layer["layer"]   # save English
            layer["layer"] = t(layer["layer"])   # translated

    return data