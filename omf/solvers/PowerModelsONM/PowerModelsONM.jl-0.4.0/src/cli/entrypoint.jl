import PowerModelsONM

if isinteractive() == false
    PowerModelsONM.entrypoint(PowerModelsONM.parse_commandline())
end
