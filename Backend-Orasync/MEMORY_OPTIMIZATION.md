# Memory Optimization Guide for Liroo Backend

This guide addresses the memory issues that can cause Cloud Run crashes and provides solutions to optimize memory usage.

## Problem Analysis

The Cloud Run service was experiencing SIGKILL crashes due to memory exhaustion during image generation operations. The main causes were:

1. **Large Image Processing**: PIL operations with high-resolution images
2. **Concurrent Requests**: Multiple simultaneous image generations
3. **Memory Leaks**: Inefficient cleanup of image buffers and objects
4. **Resource Limits**: 2GB memory limit was insufficient for heavy operations

## Implemented Solutions

### 1. Enhanced Memory Management

- **Memory Monitoring**: Real-time memory usage tracking with `psutil`
- **Automatic Cleanup**: Garbage collection triggers at memory thresholds
- **Safe Image Processing**: Optimized PIL operations with size limits
- **Buffer Management**: Proper cleanup of image buffers and objects

### 2. Cloud Run Configuration Updates

```bash
# Updated deployment settings
--memory 4Gi          # Increased from 2Gi to 4Gi
--concurrency 40      # Reduced from 80 to prevent overload
--max-instances 5     # Limited for cost control
--min-instances 0     # Allow cold starts for cost savings
```

### 3. Code Optimizations

#### Memory Thresholds
```python
MEMORY_LIMIT_MB = 1500      # Hard limit at 1.5GB
MEMORY_WARNING_MB = 1000    # Warning at 1GB
FORCE_GC_THRESHOLD_MB = 1200 # Force cleanup at 1.2GB
```

#### Safe Image Processing
- Image size limits (1024x1024 max)
- RGBA to RGB conversion
- Optimized PNG compression
- Immediate buffer cleanup

#### Comic Panel Limits
- Reduced max panels from 10 to 8
- Increased delays between panels (5 seconds)
- Memory checks before each panel generation

## Monitoring Endpoints

### Health Check
```bash
GET /health
```
Returns memory usage and status:
```json
{
  "status": "healthy",
  "memory_usage_mb": 245.67,
  "memory_warning": false,
  "memory_critical": false,
  "timestamp": "2025-01-11T17:52:50.185Z"
}
```

### Memory Status
```bash
GET /memory
```
Detailed memory information:
```json
{
  "memory_usage_mb": 245.67,
  "memory_warning_threshold_mb": 1000,
  "memory_limit_mb": 1500,
  "memory_status": "normal",
  "memory_details": {
    "rss_mb": 245.67,
    "vms_mb": 512.34,
    "percent": 6.14
  },
  "psutil_available": true,
  "timestamp": "2025-01-11T17:52:50.185Z"
}
```

## Deployment Instructions

### 1. Update Environment Variables
```bash
# In Google Cloud Console > Cloud Run > Edit & Deploy New Revision
GENAI_API_KEY=your-actual-api-key
GCS_BUCKET_NAME=your-bucket-name
BASE_URL=https://your-service-url
```

### 2. Deploy with New Configuration
```bash
./deploy-cloud-run.sh
```

### 3. Monitor Deployment
```bash
# View logs
gcloud run services logs tail liroo-backend --region us-central1

# Check memory usage
curl https://your-service-url/memory
```

## Troubleshooting

### High Memory Usage
1. **Check current usage**: `GET /memory`
2. **Monitor logs**: Look for memory warnings
3. **Reduce concurrency**: Lower concurrent requests
4. **Increase memory**: If consistently high, consider 6Gi or 8Gi

### Memory Crashes Still Occurring
1. **Check image sizes**: Ensure images aren't too large
2. **Monitor panel count**: Reduce max panels if needed
3. **Add delays**: Increase delays between operations
4. **Review logs**: Look for memory leak patterns

### Performance Optimization
1. **Image caching**: Consider caching generated images
2. **Batch processing**: Process multiple images in batches
3. **Async processing**: Use background tasks for heavy operations
4. **CDN**: Use Cloud CDN for image delivery

## Cost Considerations

### Memory vs Cost
- **2Gi**: ~$0.00002400 per 100ms
- **4Gi**: ~$0.00004800 per 100ms
- **8Gi**: ~$0.00009600 per 100ms

### Optimization Strategies
1. **Right-size memory**: Start with 4Gi, adjust based on usage
2. **Limit instances**: Use max-instances to control costs
3. **Cold starts**: Set min-instances to 0 for cost savings
4. **Monitor usage**: Use Cloud Monitoring to track costs

## Best Practices

### Development
1. **Test locally**: Use Docker with memory limits
2. **Profile memory**: Use memory profiling tools
3. **Monitor early**: Add memory checks in development
4. **Optimize images**: Compress and resize images appropriately

### Production
1. **Set alerts**: Configure memory usage alerts
2. **Monitor logs**: Watch for memory warnings
3. **Scale gradually**: Increase resources as needed
4. **Backup strategy**: Have fallback for memory issues

## Emergency Procedures

### If Service Crashes
1. **Check logs**: `gcloud run services logs read liroo-backend --region us-central1`
2. **Monitor memory**: Check `/memory` endpoint
3. **Reduce load**: Temporarily reduce concurrent requests
4. **Scale up**: Increase memory allocation if needed

### Rollback Plan
1. **Previous version**: Deploy previous working version
2. **Reduce features**: Disable image generation temporarily
3. **Manual scaling**: Reduce concurrency and instances
4. **Contact support**: If issues persist

## Future Improvements

1. **Image optimization**: Implement better image compression
2. **Caching layer**: Add Redis for image caching
3. **Async processing**: Move heavy operations to background tasks
4. **Auto-scaling**: Implement intelligent auto-scaling based on memory usage
5. **CDN integration**: Use Cloud CDN for better image delivery

## Support

For memory-related issues:
1. Check this guide first
2. Review Cloud Run logs
3. Monitor memory endpoints
4. Contact the development team with specific error messages and memory usage data 