# Tiltfile for local Kubernetes development with k3d

# Build backend image
docker_build(
    'budget-machine-backend',
    '.',
    dockerfile='backend/Dockerfile',
)

# Render Helm chart to YAML with local values
helm_cmd = [
    'helm', 'template', 'budget-machine', './infra/helm',
    '--values', 'infra/helm/values.yaml',
    '--set', 'image.repository=budget-machine-backend',
    '--set', 'image.tag=dev',
    '--set', 'env.DATABASE_URL=%s' % os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./app.db'),
    '--set', 'env.SECRET_KEY=%s' % os.getenv('SECRET_KEY', 'secret'),
]

k8s_yaml(local(' '.join(helm_cmd)))

# Expose service locally
k8s_resource('budget-machine-budget-machine', port_forwards=8000)
