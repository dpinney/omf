"turns any fields that is not a number into a string"
function _sanitize_results_metadata!(metadata::Dict{String,<:Any})::Dict{String,Any}
    for (k,v) in metadata
        if !(typeof(v) <: Real)
            metadata[k] = string(v)
        end
    end

    return metadata
end
