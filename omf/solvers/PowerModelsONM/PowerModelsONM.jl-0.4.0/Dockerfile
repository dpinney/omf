FROM julia:latest

# Julia env
ADD Project.toml /
ADD Manifest.toml /

# Source code
ADD src /src

# Instantiate Julia Env
RUN julia -O3 --color=yes --compiled-modules=yes --sysimage-native-code=yes --project=/ -e 'using Pkg; Pkg.instantiate(); Pkg.build();'

# PackageCompiler
RUN julia -q --project=/ -e 'using PackageCompiler; create_sysimage([:PowerModelsONM, :InfrastructureModels, :PowerModels, :PowerModelsDistribution, :Ipopt, :JSON, :ArgParse]; replace_default=true, cpu_target="generic");'

# Set entrypoint
ENTRYPOINT [ "julia", "--sysimage-native-code=yes", "--project=/", "/src/cli/entrypoint.jl" ]
