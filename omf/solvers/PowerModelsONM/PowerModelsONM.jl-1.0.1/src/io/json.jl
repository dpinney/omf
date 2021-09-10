"""
    load_schema(file::String)::JSONSchema.Schema

Loads a JSON Schema for validation, fixing the ref paths inside the schemas on load
"""
function load_schema(file::String)::JSONSchema.Schema
    return JSONSchema.Schema(JSON.parsefile(file); parent_dir=joinpath(dirname(pathof(PowerModelsONM)), ".."))
end
