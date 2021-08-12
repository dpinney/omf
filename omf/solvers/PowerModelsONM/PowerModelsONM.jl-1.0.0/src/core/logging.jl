"""
    _make_filtered_logger(mods::Vector, level::Logging.LogLevel)

Helper function to create the filtered logger for PMD
"""
function _make_filtered_logger(mods::Vector{<:Module}, level::Logging.LogLevel)
    LoggingExtras.EarlyFilteredLogger(_LOGGER) do log
        if any(log._module == mod for mod in mods) && log.level < level
            return false
        else
            return true
        end
    end
end


"""
    setup_logging!(args::Dict{String,<:Any})

Configures logging based on runtime arguments, for use inside [`entrypoint`](@ref entrypoint)
"""
function setup_logging!(args::Dict{String,<:Any})
    if get(args, "quiet", false)
        set_log_level!(:Error)
    elseif get(args, "verbose", false)
        set_log_level!(:Info)
    elseif get(args, "debug", false)
        set_log_level!(:Debug)
    else
        set_log_level!(:Warn)
    end
end


"""
    set_log_level!(level::Symbol)

Configures logging based `level`, `:Error`, `:Warn`, `:Info`, or `:Debug`
"""
function set_log_level!(level::Symbol)
    mods = [PowerModelsDistribution, PowerModelsProtection, PowerModelsStability, Juniper, JSONSchema]
    if level == :Error
        loglevel = Logging.Error
        push!(mods, PowerModelsONM)

        # TODO remove need for Memento
        PMD._IM.silence()
    elseif level == :Info
        loglevel = Logging.Info
    elseif level == :Debug
        loglevel = Logging.Debug
    else
        loglevel = Logging.Error

        # TODO remove need for Memento
        PMD._IM.silence()
    end

    Logging.global_logger(_make_filtered_logger(mods, loglevel))
end


"""
    silence!()

Sets logging level to "quiet"
"""
function silence!()
    set_log_level!(:Error)
end
