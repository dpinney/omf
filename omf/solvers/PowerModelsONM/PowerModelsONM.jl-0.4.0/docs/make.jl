using Documenter
using PowerModelsONM

makedocs(
    sitename = "PowerModelsONM",
    format = Documenter.HTML(),
    modules = [PowerModelsONM]
)

# Documenter can also automatically deploy documentation to gh-pages.
# See "Hosting Documentation" and deploydocs() in the Documenter manual
# for more information.
#=deploydocs(
    repo = "<repository url>"
)=#
